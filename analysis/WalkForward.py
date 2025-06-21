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
from utils.utils import unpack, save
from utils.metrics import *

class WalkForward():

    def __init__(self, num_months, percent, runs, data, opt, path):

        self.num_months = num_months
        self.percent = percent
        self.runs = runs
        self.data = data
        self.opt = opt
        self.path = path

        self.best_params = None
        self.best_fitness = None

        # isolate training and testing sets
        self.IS_len = round(len(data) / ((percent / 100) * runs + 1))
        self.OS_len = round((percent / 100) * self.IS_len)

        # init metrics with header
        self.metrics = init_walk_forward_metrics(self)

        # init indicators
        self.indicators = unpack('indicators', self.path)

    def in_sample(self, run):

        # isolate training xet
        IS_len = self.IS_len
        OS_len = self.OS_len
        IS_start = run * OS_len
        IS_end = IS_start + IS_len

        # mask dataset, one dataset each core
        IS_data = self.data.iloc[IS_start : IS_end]
        IS_indicators = self.indicators.iloc[IS_start : IS_end]

        # run exhaustive sweep
        analyzer = Analyzer(run, IS_data, IS_indicators, self.opt, self.path)
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
        OS_indicators = self.indicators.iloc[OS_start : OS_end]

        # get fittest params from in-sample analyzer
        IS_path = self.path + '/' + str(run)
        fittest = unpack('analyzer', IS_path)['fittest']

        # create and save engine for each fitness
        for fitness in tqdm(
            iterable = Fitness,
            disable = run != 0, # show only 1 core
            colour = '#4287f5',
            bar_format = '        Out-of-sample:  {percentage:3.0f}%|{bar:100}{r_bar}'):

            # extract params of fittest engine
            fittest_metric = fittest[fitness]
            params = unpack(str(fittest_metric.id), IS_path)['params']

            # run strategy blind with best params
            strategy = FastStrategy(OS_data, OS_indicators, params)
            engine = Engine(
                id = run,
                strategy = strategy)
            engine.run()

            OS_path = self.path + '/' + fitness.value
            engine.save(OS_path, True)

    ''' must call after all threads complete '''
    def build_composite(self, fitness):

        # get params from last in-sample analyzer
        IS_path = self.path + '/' + str(self.runs)
        fittest = unpack('analyzer', IS_path)['fittest']

        # extract params of fittest engine
        metric = fittest[fitness]
        params = unpack(str(metric.id), IS_path)['params']

        # build composite engine
        cash_series, trades, efficiency_sum = pd.Series(), [], 0

        # loop out-of-sample
        for run in tqdm(
            iterable = range(self.runs),
            disable = fitness is not Fitness.DRAWDOWN_PER_PROFIT, # show only 1 core
            colour = '#4287f5',
            bar_format = '        Composite:      {percentage:3.0f}%|{bar:100}{r_bar}'):

            OS_path = self.path + '/' + fitness.value

            # extract saved OS engine results
            _cash_series = unpack(run, OS_path)['cash_series']
            _trades = unpack(run, OS_path)['trades']
            _metrics = unpack(run, OS_path)['metrics']

            # cumulative cash series
            initial_cash = _cash_series.values[0]
            if len(cash_series) > 0:
                last_balance = cash_series.values[-1]
                _cash_series += last_balance - initial_cash

            cash_series = cash_series._append(_cash_series)
            trades.extend(_trades)

        # reindex trades
        for i, trade in enumerate(trades):
            trade.id = i + 1 # 1-based index for tradingview

        # mask data to OS sample
        OS_data = self.data.loc[cash_series.index, :]
        OS_indicators = self.indicators.loc[cash_series.index, :]

        # create engine, but don't run!
        strategy = FastStrategy(OS_data, OS_indicators, params)
        engine = Engine(fitness.value, strategy)

        # finish engine build
        engine.cash_series = cash_series
        engine.trades = trades
        engine.analyze() # generate metrics

        engine.save(self.path, True)

    ''' must call after all composites finished'''
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
