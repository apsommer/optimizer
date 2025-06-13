import os
import pickle

import pandas as pd
from tqdm import tqdm

from analysis.Engine import Engine
from model.Fitness import Fitness
from utils.MetricUtils import *
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, id, fitness, data, avgs, path):

        self.id = id
        self.fitness = fitness
        self.data = data
        self.avgs = avgs
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
            slowMinutes = 2555,
            slowAngleFactor = 20,
            coolOffMinutes = 5)

        self.fastMomentumMinutes = np.arange(55, 131, 5)
        self.takeProfitPercent = np.arange(.25, .70, .05)

    def run(self):

        data = self.data
        params = self.params

        id = 0
        total = len(self.fastMomentumMinutes) * len(self.takeProfitPercent)

        with tqdm(
            total = total,
            colour = 'BLUE',
            bar_format = '      {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            for fastMomentumMinutes in self.fastMomentumMinutes:
                for takeProfitPercent in self.takeProfitPercent:

                    if id > 1:
                        break

                    # update params
                    params.fastMomentumMinutes = fastMomentumMinutes
                    params.takeProfitPercent = takeProfitPercent

                    # create strategy and engine
                    strategy = LiveStrategy(data, self.avgs, params)
                    engine = Engine(id, strategy)

                    # run and save
                    engine.run()
                    engine.save(self.path)
                    id += 1

                    pbar.update(id)

        pbar.close()
        self.analyze()

    def analyze(self):

        # get num of files in dir
        num_engines = len(os.listdir(self.path))
        ids = np.arange(0, num_engines, 1)

        # collect engine metrics
        for id in ids:
            result = load_result(id, self.path)
            metrics = result['metrics']
            self.results.append(metrics)

        # todo persist all fitness params
        # todo rebuild all composite OS
        # persist best params
        metric = get_analyzer_fitness_metric(self, self.fitness)[0]
        self.params = load_result(metric.id, self.path)['params']

        self.metrics = (
            get_analyzer_metrics(self, metric.id) +
            get_analyzer_fitness_metric(self, Fitness.MAX_PROFIT) +
            get_analyzer_fitness_metric(self, Fitness.MAX_EXPECTANCY) +
            get_analyzer_fitness_metric(self, Fitness.MAX_WIN_RATE) +
            get_analyzer_fitness_metric(self, Fitness.MAX_AVERAGE_WIN) +
            get_analyzer_fitness_metric(self, Fitness.MIN_AVERAGE_LOSS) +
            get_analyzer_fitness_metric(self, Fitness.MIN_DRAWDOWN) +
            get_analyzer_fitness_metric(self, Fitness.MIN_DRAWDOWN_PER_PROFIT)
        )

    def rebuild_engine(self, id):

        data = self.data

        result = load_result(id, self.path)
        params = result['params']

        strategy = LiveStrategy(data, self.avgs, params)

        # init but not run
        engine = Engine(id, strategy)

        # unpack previously completed result
        engine.id = result['id']
        engine.params = params
        engine.metrics = result['metrics']
        engine.trades = result['trades']
        engine.cash_series = result['cash_series']

        return engine

    ''' serialize '''
    def save(self):

        path = self.path

        result = {
            'id': self.id,
            'params': self.params,
            'metrics': self.metrics
        }

        # make directory, if needed
        if not os.path.exists(path):
            os.makedirs(path)

        # create new binary
        filename = 'analyzer' + '.bin'
        path_filename = path + '/' + filename

        filehandler = open(path_filename, 'wb')
        pickle.dump(result, filehandler)

########################################################################################################################

''' deserialize '''
def load_result(id, path):

    filename = str(id) + '.bin'
    path_filename = path + '/' + filename

    try:
        filehandler = open(path_filename, 'rb')
        return pickle.load(filehandler)

    except FileNotFoundError:
        print(f'\n{path_filename} not found')
        exit()

