import os
import shutil

import pandas as pd
from tqdm import tqdm

from analysis.Analyzer import Analyzer
from analysis.Engine import Engine
from model.Fitness import Fitness
from strategy.LiveStrategy import LiveStrategy
from utils.utils import load_result
from utils.metrics import *

class WalkForward():

    def __init__(self, num_months, percent, runs, data, opt):
        self.num_months = num_months
        self.percent = percent
        self.runs = runs
        self.data = data
        self.opt = opt
        self.params = None
        self.best_fitness = None

        # organize outputs
        data_name = 'NQ_' + str(num_months) + 'mon'
        self.path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'

        # remove any residual analyses
        shutil.rmtree(self.path, ignore_errors=True)

        # isolate training and testing sets
        self.IS_len = round(len(data) / ((percent / 100) * runs + 1))
        self.OS_len = round((percent / 100) * self.IS_len)

        # init metrics with header
        self.metrics = get_walk_forward_init_metrics(self)

        # init exponential averages
        self.calculate_avgs()

    def calculate_avgs(self):

        fastMinutes = 25
        slowMinutes = 2555

        data = self.data

        # calculate raw averages
        rawFast = pd.Series(data.Open).ewm(span=fastMinutes).mean()
        rawSlow = pd.Series(data.Open).ewm(span=slowMinutes).mean()
        fast = rawFast.ewm(span=5).mean()
        slow = rawSlow.ewm(span=200).mean()
        fastSlope = get_slope(fast)
        slowSlope = get_slope(slow)

        # persist
        self.avgs = pd.DataFrame(index=data.index)
        self.avgs['fast'] = fast
        self.avgs['slow'] = slow
        self.avgs['fastSlope'] = fastSlope
        self.avgs['slowSlope'] = slowSlope

    def sweep_IS(self, run):

        path = self.path + str(run) + '/'
        IS_len = self.IS_len
        OS_len = self.OS_len
        data = self.data

        # isolate training xet
        IS_start = run * OS_len
        IS_end = IS_start + IS_len
        IS = data.iloc[IS_start : IS_end]

        # run exhaustive sweep over IS
        analyzer = Analyzer(run, IS, self.avgs, self.opt, path)
        analyzer.run()
        analyzer.save()
        # print_metrics(analyzer.metrics)

    def run_OS(self, run):

        IS_len = self.IS_len
        OS_len = self.OS_len
        data = self.data

        IS_start = run * OS_len
        IS_end = IS_start + IS_len

        OS_start = IS_end
        OS_end = OS_start + OS_len
        OS = data.iloc[OS_start:OS_end]

        # get fittest params from last IS analyzer
        IS_path = self.path + str(run)
        fittest = load_result('analyzer', IS_path)['fittest']

        for fitness in tqdm(
            iterable = Fitness,
            disable = run != 0,
            # leave = fitness == Fitness.DRAWDOWN_PER_PROFIT,
            # position = self.id,
            colour = '#4287f5',
            bar_format = '        Out-of-sample:  {percentage:3.0f}%|{bar:100}{r_bar}'):

            # extract params of fittest engine
            fittest_metric = fittest[fitness]
            params = load_result(str(fittest_metric.id), IS_path)['params']
            metrics = load_result(str(fittest_metric.id), IS_path)['metrics']

            # run strategy blind over OS with best params
            strategy = LiveStrategy(OS, self.avgs, params)
            engine = Engine(run, strategy)
            engine.run()

            # calculate efficiency relative to companion IS
            for metric in metrics:
                if metric.name == 'annual_return':
                    IS_annual = metric.value

            for metric in engine.metrics:
                if metric.name == 'annual_return':
                    OS_annual = metric.value

            efficiency = (OS_annual / IS_annual) * 100
            efficiency_metric = Metric('efficiency', efficiency, '%', 'Efficiency', None, engine.id)
            engine.metrics.append(efficiency_metric)

            OS_path = self.path + fitness.value + '/'
            engine.save(OS_path, True)

        # print results
        # print_metrics(engine.metrics)
        # engine.print_trades()

    ''' must call after all threads complete '''
    def build_composite(self, fitness):

        data = self.data

        # get params from last IS
        IS_path = self.path + str(self.runs)
        fittest = load_result('analyzer', IS_path)['fittest']

        # extract params of fittest engine
        metric = fittest[fitness]
        params = load_result(str(metric.id), IS_path)['params']

        # build composite engine
        cash_series, trades, efficiency_sum = pd.Series(), [], 0

        for run in tqdm(
            iterable = range(self.runs),
            disable = fitness is not Fitness.DRAWDOWN_PER_PROFIT,
            # leave = fitness == Fitness.DRAWDOWN_PER_PROFIT,
            # position = self.id,
            colour = '#4287f5',
            bar_format = '        Composite:      {percentage:3.0f}%|{bar:100}{r_bar}'):

            OS_path = self.path + fitness.value + '/'

            # extract saved OS engine results
            OS_cash_series = load_result(run, OS_path)['cash_series']
            OS_trades = load_result(run, OS_path)['trades']
            OS_metrics = load_result(run, OS_path)['metrics']

            initial_cash = OS_cash_series.values[0]

            # todo engine efficiency error?
            for metric in OS_metrics:
                if metric.name == 'efficiency':
                    efficiency_sum += metric.value

            if len(cash_series) > 0:

                last_balance = cash_series.values[-1]
                OS_cash_series += last_balance - initial_cash

            cash_series = cash_series._append(OS_cash_series)
            trades.extend(OS_trades)

        # reindex trades
        for i, trade in enumerate(trades):
            trade.id = i + 1 # 1-based index

        # mask data to OS sample
        OS = data.loc[cash_series.index, :]

        # create engine, but don't run!
        strategy = LiveStrategy(OS, self.avgs, params)
        engine = Engine(fitness.value, strategy)

        # finish engine build
        engine.cash_series = cash_series
        engine.trades = trades
        engine.analyze() # generate metrics

        # todo calculate efficiency, add to metrics
        efficiency = efficiency_sum / self.runs
        efficiency_metric = Metric('efficiency', efficiency, '%', 'Efficiency', None, engine.id)
        engine.metrics.append(efficiency_metric)

        engine.save(self.path, True)

    ''' must call after all composites finished'''
    def analyze(self):

        # isolate composite with highest profit
        highest_profit = -np.inf
        for fitness in Fitness:

            result = load_result(fitness.value, self.path[:-1])  # todo fix path
            cash_series = result['cash_series']
            cash = cash_series[-1]

            if cash > highest_profit:
                highest_profit = cash
                self.params = result['params']
                self.best_fitness = fitness

        self.metrics += get_walk_forward_results_metrics(self)

def get_slope(series):

    slope = pd.Series(index=series.index)
    prev = series.iloc[0]

    for idx, value in series.items():
        if idx == series.index[0]: continue
        slope[idx] = ((value - prev) / prev) * 100
        prev = value

    return np.rad2deg(np.atan(slope))