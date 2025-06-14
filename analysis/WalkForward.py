import os
import shutil

import pandas as pd

from analysis.Analyzer import Analyzer, load_result
from analysis.Engine import Engine
from model.Fitness import Fitness
from strategy.LiveStrategy import LiveStrategy
from utils.MetricUtils import *

class WalkForward():

    def __init__(self, num_months, percent, runs, data):
        self.num_months = num_months
        self.percent = percent
        self.runs = runs
        self.data = data
        self.params = None

        # organize outputs
        data_name = 'NQ_' + str(num_months) + 'mon'
        self.path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'

        # remove any residual analyses
        shutil.rmtree(self.path, ignore_errors=True)

        # isolate training and testing sets
        self.IS_len = round(len(data) / ((percent / 100) * runs + 1))
        self.OS_len = round((percent / 100) * self.IS_len)

        # init metrics with header
        self.metrics = get_walk_forward_header_metrics(self)

        # init exponential averages
        self.calculate_avgs()

    def calculate_avgs(self):

        data = self.data
        fastMinutes = 25
        slowMinutes = 2555

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

    def walk_forward(self, run):

        # sweep in-sample
        self.sweep_IS(run)

        # skip OS on last run
        if run == self.runs:
            return

        # run out-of-sample
        self.run_OS(run)

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
        analyzer = Analyzer(run, IS, self.avgs, path)
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

        for fitness in Fitness:

            # extract params of fittest engine
            metric = fittest[fitness]
            params = load_result(str(metric.id), IS_path)['params']

            OS_path = self.path + fitness.value + '/'

            # run strategy blind over OS with best params
            strategy = LiveStrategy(OS, self.avgs, params)
            engine = Engine(run, strategy)
            engine.run()
            engine.save(OS_path)

        # print results
        # print_metrics(engine.metrics)
        # engine.print_trades()

    ''' must call after all threads complete '''
    def build_composites(self):

        data = self.data

        # get params from last IS
        IS_path = self.path + str(self.runs)
        fittest = load_result('analyzer', IS_path)['fittest']

        # build composite for each fitness function
        for fitness in Fitness:

            # extract params of fittest engine
            metric = fittest[fitness]
            params = load_result(str(metric.id), IS_path)['params']

            # build composite engine
            cash_series, trades, bal = pd.Series(), [], 0
            for run in range(self.runs):

                OS_path = self.path + fitness.value + '/'

                # extract saved OS engine results
                OS_cash_series = load_result(run, OS_path)['cash_series']
                OS_trades = load_result(run, OS_path)['trades']
                initial_cash = OS_cash_series.values[0]

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
            engine.analyze()
            engine.save(self.path)

        # todo
        # self.analyze()

    def analyze(self):
        self.metrics += get_walk_forward_metrics(self)

def get_slope(series):

    slope = pd.Series(index=series.index)
    prev = series.iloc[0]

    for idx, value in series.items():
        if idx == series.index[0]: continue
        slope[idx] = ((value - prev) / prev) * 100
        prev = value

    return np.rad2deg(np.atan(slope))