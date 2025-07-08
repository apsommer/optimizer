import os
import pickle
import shutil
from datetime import timezone

import pandas as pd
from numpy import linspace
from tqdm import tqdm

from analysis.Engine import Engine
from analysis.Analyzer import Analyzer
from model.Fitness import Fitness
from rebuild_wfa import best_fitness
from strategy.FastStrategy import FastStrategy
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils import utils
from utils.constants import *
from utils.utils import *
from utils.metrics import *
import finplot as fplt

class WalkForward():

    def __init__(self, num_months, percent, runs, data, emas, fractals, opt, path):

        self.num_months = num_months
        self.percent = percent
        self.runs = runs
        self.data = data
        self.emas = emas
        self.fractals = fractals
        self.opt = opt
        self.path = path

        self.best_params = None
        self.best_fitness = None

        # isolate training and testing sets
        self.IS_len = round(len(data) / ((percent / 100) * runs + 1))
        self.OS_len = round((percent / 100) * self.IS_len)

        # init metrics with header
        self.metrics = init_walk_forward_metrics(self)

    def in_sample(self, run):

        # isolate training xet
        IS_len = self.IS_len
        OS_len = self.OS_len
        IS_start = run * OS_len
        IS_end = IS_start + IS_len

        # mask dataset, one dataset each core
        IS_data = self.data.iloc[IS_start : IS_end]
        IS_emas = self.emas.iloc[IS_start : IS_end]
        IS_fractals = self.fractals.iloc[IS_start : IS_end]

        # run exhaustive sweep
        analyzer = Analyzer(run, IS_data, IS_emas, IS_fractals, self.opt, self.path)
        analyzer.run()
        analyzer.save()

    def out_of_sample(self, run):

        # isolate samples
        IS_len = self.IS_len
        OS_len = self.OS_len
        IS_start = run * OS_len
        IS_end = IS_start + IS_len
        OS_start = IS_end
        OS_end = OS_start + OS_len

        # mask dataset
        OS_data = self.data.iloc[OS_start : OS_end]
        OS_emas = self.emas.iloc[OS_start : OS_end]
        OS_fractals = self.fractals.iloc[OS_start : OS_end]

        # get fittest params from in-sample analyzer
        IS_path = self.path + '/' + str(run)
        fittest = unpack('analyzer', IS_path)['fittest']

        # todo skip extra fitness if only analyzing 1 engine
        # if len(fittest) > 0 and self.opt.size == 1:
        #     first_fitness = list(fittest.keys())[0]
        #     fittest = { first_fitness: fittest[first_fitness] }

        # create and save engine for each fitness
        for fitness in tqdm(
            iterable = fittest,
            disable = run != 0, # show only 1 core
            colour = blue,
            bar_format = '        Out-of-sample:  {percentage:3.0f}%|{bar:100}{r_bar}'):

            # extract params of fittest engine
            fittest_id = fittest[fitness].id
            IS_engine = unpack(fittest_id, IS_path)
            params = IS_engine['params']

            # run strategy blind with best params
            strategy = LiveStrategy(OS_data, OS_emas, OS_fractals, params)
            engine = Engine(
                id = run,
                strategy = strategy)
            engine.run()

            # calculate efficiency
            IS_metrics = IS_engine['metrics']
            IS_return = next((metric.value for metric in IS_metrics if metric.name == 'annual_return'), None)
            OS_return = next((metric.value for metric in engine.metrics if metric.name == 'annual_return'), None)

            # catch engine with no trades
            if OS_return is None:
                return

            eff = (OS_return / IS_return) * 100
            eff_metric = Metric('efficiency', eff, '%', 'Efficiency', formatter = None, id = run)
            engine.metrics.append(eff_metric)

            # persist full engine for out-of-sample
            OS_path = self.path + '/' + fitness.value
            engine.save(OS_path, True)

    def build_composite(self, fitness):

        # build composite engine by stitching OS runs for this fitness
        cash_series = pd.Series()
        trades = []
        effs = []
        invalids = []
        for run in tqdm(
            iterable = range(self.runs),
            disable = fitness is not Fitness.PROFIT, # show only 1 core
            colour = blue,
            bar_format = '        Composite:      {percentage:3.0f}%|{bar:100}{r_bar}'):

            OS_path = self.path + '/' + fitness.value
            OS_engine_filepath = OS_path + '/' + str(run) + '.bin'

            # check if OS run exists from profitable fittest IS
            if os.path.exists(OS_engine_filepath):

                OS_engine = unpack(run, OS_path)

                # extract saved OS engine results
                OS_cash_series = OS_engine['cash_series']
                OS_trades = OS_engine['trades']
                OS_metrics = OS_engine['metrics']

                eff_metric = next((metric for metric in OS_metrics if metric.name == 'efficiency'), None)
                effs.append(eff_metric.value)

                # cumulative cash series
                initial_cash = OS_cash_series.values[0]
                if len(cash_series) > 0:
                    last_balance = cash_series.values[-1]
                    OS_cash_series += last_balance - initial_cash

            # IS not profitable, accompanying OS does not exist
            else:

                # count invalid runs
                invalids.append(run)

                # isolate testing test
                IS_len = self.IS_len
                OS_len = self.OS_len
                IS_start = run * OS_len
                IS_end = IS_start + IS_len
                OS_start = IS_end
                OS_end = OS_start + OS_len

                # mask dataset
                mask = self.data.iloc[OS_start: OS_end]

                # create timestamps
                OS_timestamps = pd.date_range(
                    start = mask.index[0],
                    end = mask.index[-1],
                    freq = '1min'
                )

                # todo will fail if first run has no OS
                if cash_series.empty:
                    last_balance = 11000
                else:
                    last_balance = cash_series.values[-1]

                # no cash or trades
                OS_cash_series = pd.Series()
                for timestamp in OS_timestamps:
                    if timestamp not in self.data.index: continue
                    OS_cash_series[timestamp] = last_balance

                OS_trades = []

            cash_series = cash_series._append(OS_cash_series)
            trades.extend(OS_trades)

        # todo extract to new method

        # reindex trades
        for i, trade in enumerate(trades):
            trade.id = i + 1 # 1-based index for tradingview

        # get params from last in-sample analyzer
        IS_path = self.path + '/' + str(self.runs)
        fittest = unpack('analyzer', IS_path)['fittest']

        # extract params of fittest engine
        if fitness in fittest:
            metric = fittest[fitness]
            params = unpack(str(metric.id), IS_path)['params']
        else:
            params = None # todo fix, fails if last IS for this fitness was not profitable

        # mask data to OS sample
        OS_data = self.data.loc[cash_series.index, :]
        OS_emas = self.emas.loc[cash_series.index, :]
        OS_fractals = self.fractals.loc[cash_series.index, :]

        # create engine, but don't run!
        strategy = LiveStrategy(OS_data, OS_emas, OS_fractals, params)
        engine = Engine(fitness.value, strategy)

        # finish engine build
        engine.cash_series = cash_series
        engine.trades = trades
        engine.analyze() # generate metrics

        # todo efficiency
        # avg_eff = np.mean(effs)
        # print(f'fitness: {fitness}, avg_eff: {avg_eff}')

        # invalid analyzers
        if len(invalids) > 0:
            engine.metrics.append(
                Metric('invalids', str(invalids), None, 'Invalid runs'))

        # save OS composite for this fitness
        engine.save(self.path, True)

    def analyze(self):

        # isolate composite with highest profit
        highest_profit = -np.inf
        for fitness in Fitness:

            engine = unpack(fitness.value, self.path)
            cash_series = engine['cash_series']
            cash = cash_series[-1]

            if cash > highest_profit:
                highest_profit = cash
                best_params = engine['params']
                best_fitness = fitness

        self.best_params = best_params
        self.best_fitness = best_fitness

        self.metrics += get_walk_forward_results_metrics(self)

    def print_params_of_fittest_composite(self):

        best_fitness = self.best_fitness

        for run in range(self.runs):

            IS_path = self.path + '/' + str(run)
            fittest = unpack('analyzer', IS_path)['fittest']

            if best_fitness not in fittest:
                print('\t' + str(run) + ': in-sample not profitable')
                continue

            metric = fittest[best_fitness]
            params = unpack(str(metric.id), IS_path)['params']
            print('\t' + str(run) + ', [' + str(metric.id) + ']: ' + params.one_line)

    ''' serialize '''
    def save(self):

        bundle = {
            'best_params': self.best_params,
            'best_fitness': self.best_fitness,
            'metrics': self.metrics
        }

        save(
            bundle = bundle,
            filename = 'wfa',
            path = self.path)

    ####################################################################################################################

    def plot_equity(self):

        ax = init_plot(1, 'Equity')

        for fitness in Fitness:

            # unpack composite engine
            engine = unpack(fitness.value, self.path)
            params = engine['params']
            cash_series = engine['cash_series']

            # mask dataset
            start = cash_series.index[0]
            end = cash_series.index[-1]
            comp_data = self.data[start: end]
            comp_ema = self.emas[start: end]
            comp_fractals = self.fractals[start: end]

            strategy = LiveStrategy(comp_data, comp_ema, comp_fractals, params)
            composite = Engine(fitness.value, strategy)

            # deserialize previous result
            composite.id = engine['id']
            composite.params = params
            composite.metrics = engine['metrics']
            composite.trades = engine['trades']
            composite.cash_series = cash_series
            composite.cash = cash_series[-1]

            # plot cash series
            fplt.plot(cash_series, color=fitness.color, legend=fitness.pretty, ax=ax)

            # plot selected fitness composite
            if fitness is self.best_fitness:
                composite.print_metrics()
                composite.print_trades()
                composite.plot_trades()

            # only calc once
            if fitness is Fitness.PROFIT:

                # plot initial cash
                fplt.plot(composite.initial_cash, color=dark_gray, ax=ax)

                # reference simple buy and hold
                size = composite.strategy.size
                point_value = composite.strategy.ticker.point_value
                # delta_df = composite.data.Close - composite.data.Close.iloc[0]
                delta_df = self.data.Close - self.data.Close.iloc[0]
                initial_cash = composite.initial_cash
                buy_hold = size * point_value * delta_df + initial_cash

                # plot buy and hold
                fplt.plot(buy_hold, color=dark_gray, ax=ax)

            # superimpose OS windows
            for run in range(self.runs):

                # isolate samples
                IS_len = self.IS_len
                OS_len = self.OS_len
                IS_start = run * OS_len
                IS_end = IS_start + IS_len
                OS_start = IS_end

                idx = self.data.index[OS_start]
                fplt.add_line((idx, 0), (idx, 1e6), width = 1, color = light_gray, ax=ax)

        fplt.show()