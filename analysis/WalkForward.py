import os
import shutil

import pandas as pd

from analysis.Analyzer import Analyzer, load_result
from analysis.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils.MetricUtils import *

class WalkForward():

    def __init__(self, num_months, percent, runs, fitness, data):
        self.num_months = num_months
        self.percent = percent
        self.runs = runs
        self.fitness = fitness
        self.data = data
        self.params = None

        # organize outputs
        data_name = 'NQ_' + str(num_months) + 'mon'
        self.path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'

        # remove any residual analyses
        shutil.rmtree(self.path, ignore_errors=True)

        # isolate training and testing sets
        self.IS_len = int(len(data) / ((percent / 100) * runs + 1))
        self.OS_len = int((percent / 100) * self.IS_len)

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
        params = self.sweep_IS(run)

        # skip last run out-of-sample
        if run == self.runs: return

        # run out-of-sample single engine
        self.run_OS(run, params)

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
        analyzer = Analyzer(run, self.fitness, IS, self.avgs, path)
        analyzer.run()
        analyzer.save()
        # print_metrics(analyzer.metrics)

        return analyzer.params

    def run_OS(self, run, params):

        IS_len = self.IS_len
        OS_len = self.OS_len
        data = self.data

        IS_start = run * OS_len
        IS_end = IS_start + IS_len

        OS_start = IS_end
        OS_end = OS_start + OS_len
        OS = data.iloc[OS_start:OS_end]

        # run strategy blind over OS with best params
        strategy = LiveStrategy(OS, self.avgs, params)
        engine = Engine(run, strategy)
        engine.run()
        engine.save(self.path)

        # print results
        # print_metrics(engine.metrics)
        # engine.print_trades()

    ''' must call after all threads complete '''
    def build_composite(self):

        runs = self.runs
        path = self.path
        data = self.data

        # get params from last IS
        IS_path = self.path + str(runs)
        params = load_result('analyzer', IS_path)['params']
        self.params = params

        # build composite engine
        cash_series = pd.Series()
        trades = []
        for run in range(runs):

            OS_cash_series = load_result(run, path)['cash_series']
            OS_trades = load_result(run, path)['trades']

            cash_series = cash_series._append(OS_cash_series)
            trades.extend(OS_trades)

        # reindex trades
        for i, trade in enumerate(trades):
            trade.id = i + 1 # 1-based index

        # mask data to OS sample
        OS = data.loc[cash_series.index, :]

        # create engine, but don't run!
        strategy = LiveStrategy(OS, self.avgs, params)
        engine = Engine('Out-of-sample composite', strategy)

        # finish engine build
        engine.cash_series = cash_series
        engine.trades = trades
        engine.analyze()
        engine.save(self.path)

        self.analyze()
        return engine

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