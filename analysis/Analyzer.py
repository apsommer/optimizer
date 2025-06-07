import os
import pickle

import pandas as pd

from analysis.Engine import Engine
from model.Metric import Metric
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, data, path):

        self.data = data
        self.path = path

        self.engine_metrics = []
        self.metrics = []

        self.params = LiveParams(
            fastMinutes = 25,
            disableEntryMinutes = 105,
            fastMomentumMinutes = None,
            fastCrossoverPercent = 0,
            takeProfitPercent = None,
            fastAngleFactor = 15,
            slowMinutes = None,
            slowAngleFactor = 20,
            coolOffMinutes = 5)

        self.fastMomentumMinutes = np.arange(55, 140, 5)
        self.takeProfitPercent = np.arange(.25, .80, .05)
        self.slowMinutes = np.arange(1555, 2655, 100)

    def run(self):

        data = self.data
        params = self.params

        id = 0
        for fastMomentumMinutes in self.fastMomentumMinutes:
            for takeProfitPercent in self.takeProfitPercent:
                for slowMinutes in self.slowMinutes:

                    # todo temp
                    if id > 2: break

                    # update params
                    params.fastMomentumMinutes = fastMomentumMinutes
                    params.takeProfitPercent = takeProfitPercent
                    params.slowMinutes = slowMinutes

                    # create strategy and engine
                    strategy = LiveStrategy(data, params)
                    engine = Engine(id=id, strategy=strategy)

                    # run and save
                    engine.run()
                    engine.save(self.path)
                    id += 1

        self.analyze()

    def analyze(self):

        # get num of files in dir
        num_engines = len(os.listdir(self.path))
        ids = np.arange(0, num_engines, 1)

        # collect engine results
        for id in ids:

            result = self.load_result(id)
            metrics = result['metrics']
            self.engine_metrics.append(metrics)

        metrics = get_max_profit(self.engine_metrics)
        self.metrics = metrics

        # results.loc[id, 'profit'] = result['metrics']['profit'].value
        # results.loc[id, 'max_drawdown'] = result['metrics']['max_drawdown'].value
        # results.loc[id, 'profit_factor'] = result['metrics']['profit_factor'].value
        # results.loc[id, 'drawdown_per_profit'] = result['metrics']['drawdown_per_profit'].value
        # results.loc[id, 'expectancy'] = result['metrics']['expectancy'].value
        # results.loc[id, 'trades_per_day'] = result['metrics']['trades_per_day'].value

    def print_metrics(self):

        results = self.engine_metrics

        print()

        max_profit = np.max(results.profit)
        idx = results[results.profit == max_profit].index.values[0]
        print(f'max_profit: {round(max_profit)}, e{idx}')

        min_drawdown = np.min(results.max_drawdown)
        idx = results[results.max_drawdown == min_drawdown].index.values[0]
        print(f'min_drawdown: {round(min_drawdown)}, e{idx}')

        max_pf = np.max(results.profit_factor)
        idx = results[results.profit_factor == max_pf].index.values[0]
        print(f'max_pf: {max_pf}, e{idx}')

        min_dpp = np.min(results.drawdown_per_profit)
        idx = results[results.drawdown_per_profit == min_dpp].index.values[0]
        print(f'min_dpp: {round(min_dpp)}, e{idx}')

        max_expectancy = np.max(results.expectancy)
        idx = results[results.expectancy == max_expectancy].index.values[0]
        print(f'max_expectancy: {round(max_expectancy, 2)}, e{idx}')

        min_trades_per_day = np.min(results.trades_per_day)
        idx = results[results.trades_per_day == min_trades_per_day].index.values[0]
        print(f'min_trades_per_days: {round(min_trades_per_day, 2)}, e{idx}')

        print()

    def rebuild_engine(self, id):

        data = self.data
        result = self.load_result(id)
        params = result['params']

        strategy = LiveStrategy(data, params)
        engine = Engine(id, strategy)

        engine.run()
        return engine

    ''' deserialize '''
    def load_result(self, id):

        filename = 'e' + str(id) + '.bin'
        path_filename = self.path + '/' + filename
        filehandler = open(path_filename, 'rb')

        try:
            pickle.load(filehandler)
        except FileNotFoundError:
            print(f'{path_filename} not found')
        return

def get_max_profit(engine_metrics):

    for metrics in engine_metrics:
        for metric in metrics:
            if metric.name == 'profit':
                print(metric.value)

    max_profit = 100
    num = 1
    # max_profit = np.max(engine_metrics['profit'].value)
    # num = engine_metrics[engine_metrics.profit == max_profit].index.values[0]
    return [Metric('max_profit', max_profit, str(num), 'Max profit')]