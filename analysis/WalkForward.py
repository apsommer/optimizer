import os
import pickle
import shutil

import pandas as pd
from numpy import linspace
from tqdm import tqdm

from analysis.Analyzer import Analyzer
from analysis.Engine import Engine
from model.Fitness import Fitness
from strategy.FastStrategy import FastStrategy
from strategy.LiveStrategy import LiveStrategy
from utils import utils
from utils.constants import *
from utils.utils import *
from utils.metrics import *
import finplot as fplt

class WalkForward():

    def __init__(self, num_months, percent, runs, data, emas, slopes, fractals, opt, path):

        self.num_months = num_months
        self.percent = percent
        self.runs = runs
        self.data = data
        self.emas = emas
        self.slopes = slopes
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
        IS_slopes = self.slopes.iloc[IS_start : IS_end]
        IS_fractals = self.fractals.iloc[IS_start : IS_end]

        # run exhaustive sweep
        analyzer = Analyzer(run, IS_data, IS_emas, IS_slopes, IS_fractals, self.opt, self.path)
        analyzer.run()
        analyzer.save()

    def out_of_sample(self, run):

        # isolate testing test
        IS_len = self.IS_len
        OS_len = self.OS_len
        IS_start = run * OS_len
        IS_end = IS_start + IS_len
        OS_start = IS_end
        OS_end = OS_start + OS_len

        # mask dataset
        OS_data = self.data.iloc[OS_start : OS_end]
        OS_emas = self.emas.iloc[OS_start : OS_end]
        OS_slopes = self.slopes.iloc[OS_start : OS_end]
        OS_fractals = self.fractals.iloc[OS_start : OS_end]

        # get fittest params from in-sample analyzer
        IS_path = self.path + '/' + str(run)
        fittest = unpack('analyzer', IS_path)['fittest']

        # create and save engine for each fitness
        for fitness in tqdm(
            iterable = Fitness,
            disable = run != 0, # show only 1 core
            colour = blue,
            bar_format = '        Out-of-sample:  {percentage:3.0f}%|{bar:100}{r_bar}'):

            # extract params of fittest engine
            fittest_metric = fittest[fitness]
            params = unpack(str(fittest_metric.id), IS_path)['params']

            # run strategy blind with best params
            strategy = FastStrategy(OS_data, OS_emas, OS_slopes, OS_fractals, params)
            engine = Engine(
                id = run,
                strategy = strategy)
            engine.run()

            OS_path = self.path + '/' + fitness.value
            engine.save(OS_path, True)

    def build_composite(self, fitness):

        # get params from last in-sample analyzer
        IS_path = self.path + '/' + str(self.runs)
        fittest = unpack('analyzer', IS_path)['fittest']

        # extract params of fittest engine
        metric = fittest[fitness]
        params = unpack(str(metric.id), IS_path)['params']

        # build composite engine
        cash_series = pd.Series()
        trades = []
        highest_profit = -np.nan

        # stitch OS runs
        for run in tqdm(
            iterable = range(self.runs),
            disable = fitness is not Fitness.DRAWDOWN_PER_PROFIT, # show only 1 core
            colour = blue,
            bar_format = '        Composite:      {percentage:3.0f}%|{bar:100}{r_bar}'):

            OS_path = self.path + '/' + fitness.value

            # extract saved OS engine results
            _cash_series = unpack(run, OS_path)['cash_series']
            _trades = unpack(run, OS_path)['trades']
            _metrics = unpack(run, OS_path)['metrics']

            # cumulative cash series
            initial_cash = _cash_series.values[0]
            gross_profit = _cash_series.values[-1]
            if len(cash_series) > 0:
                last_balance = cash_series.values[-1]
                _cash_series += last_balance - initial_cash

            profit = gross_profit - initial_cash
            if profit > highest_profit:
                highest_profit = profit

            cash_series = cash_series._append(_cash_series)
            trades.extend(_trades)

        # reindex trades
        for i, trade in enumerate(trades):
            trade.id = i + 1 # 1-based index for tradingview

        # mask data to OS sample
        OS_data = self.data.loc[cash_series.index, :]
        OS_emas = self.emas.loc[cash_series.index, :]
        OS_slopes = self.slopes.loc[cash_series.index, :]
        OS_fractals = self.fractals.loc[cash_series.index, :]

        # create engine, but don't run!
        strategy = FastStrategy(OS_data, OS_emas, OS_slopes, OS_fractals, params)
        engine = Engine(fitness.value, strategy)

        # finish engine build
        engine.cash_series = cash_series
        engine.trades = trades
        engine.analyze() # generate metrics

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
            comp_slopes = self.slopes[start: end]
            comp_fractals = self.fractals[start: end]

            strategy = FastStrategy(comp_data, comp_ema, comp_slopes, comp_fractals, params)
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
                composite.plot_equity()

            # only calc once
            if fitness is Fitness.PROFIT:

                # plot initial cash
                fplt.plot(composite.initial_cash, color=dark_gray, ax=ax)

                # reference simple buy and hold
                size = composite.strategy.size
                point_value = composite.strategy.ticker.point_value
                delta_df = composite.data.Close - composite.data.Close.iloc[0]
                initial_cash = composite.initial_cash
                buy_hold = size * point_value * delta_df + initial_cash

                # plot buy and hold
                fplt.plot(buy_hold, color=dark_gray, ax=ax)

        fplt.show()