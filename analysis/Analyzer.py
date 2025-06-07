import os
import pickle

import pandas as pd
from numpy.ma.core import max_filler

from analysis.Engine import Engine
from model.Metric import Metric
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, data, path):

        self.data = data
        self.path = path

        self.results = []
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
                    if id > 4: break

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

        # collect engine metrics
        for id in ids:
            result = self.load_result(id)
            metrics = result['metrics']
            self.results.append(metrics)

        self.metrics = (
            analyze_config(self) +
            analyze_metric(self, 'profit', 'max') +
            analyze_metric(self, 'expectancy', 'max') +
            analyze_metric(self, 'win_rate', 'max') +
            analyze_metric(self, 'average_win', 'max') +
            analyze_metric(self, 'average_loss', 'min') +
            analyze_metric(self, 'max_drawdown', 'min') +
            analyze_metric(self, 'drawdown_per_profit', 'min'))

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

        filename = str(id) + '.bin'
        path_filename = self.path + '/' + filename

        try:
            filehandler = open(path_filename, 'rb')
            return pickle.load(filehandler)

        except FileNotFoundError:
            print(f'\n{path_filename} not found')
            exit()

def analyze_config(analyzer):
    return [ Metric('config_header', None, None, 'Analyzer:') ]

def analyze_metric(analyzer, name, minOrMax):

    results = analyzer.results

    # isolate metric of interest
    _metrics = []
    for metrics in results:
        for metric in metrics:
            if metric.name == name:
                _metrics.append(metric)

    # get max, or min
    if minOrMax == 'max':

        max = sorted(_metrics, key=lambda metric: metric.value, reverse=True)[0]
        num = _metrics.index(max)
        max.title = '[' + str(num) + '] (Max) ' + max.title
        return [ max ]

    elif minOrMax == 'min':
        min = sorted(_metrics, key=lambda metric: metric.value, reverse=False)[0]
        num = _metrics.index(min)
        min.title = '[' + str(num) + '] (Min) ' + min.title
        return [ min ]
