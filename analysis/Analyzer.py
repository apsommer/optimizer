import os
import pickle

import pandas as pd
from tqdm import tqdm

from analysis.Engine import Engine, load_result
from model.Fitness import Fitness
from utils.MetricUtils import *
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, id, data, avgs, path):

        self.id = id
        self.data = data
        self.avgs = avgs
        self.path = path

        self.results = []
        self.metrics = []
        self.fittest = { }

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

        # persist all best params per fitness function
        self.metrics = (
            get_analyzer_metrics(self) +
            get_analyzer_fitness_metric(self, Fitness.PROFIT) +
            get_analyzer_fitness_metric(self, Fitness.EXPECTANCY) +
            get_analyzer_fitness_metric(self, Fitness.WIN_RATE) +
            get_analyzer_fitness_metric(self, Fitness.AVERAGE_WIN) +
            get_analyzer_fitness_metric(self, Fitness.AVERAGE_LOSS) +
            get_analyzer_fitness_metric(self, Fitness.DRAWDOWN) +
            get_analyzer_fitness_metric(self, Fitness.DRAWDOWN_PER_PROFIT))

        for fitness in Fitness:
            self.fittest[fitness] = self.get_fittest_metric(fitness)

    def get_fittest_metric(self, fitness):

        results = self.results
        name = fitness.value

        # isolate metric of interest
        _metrics = []
        for metrics in results:
            for metric in metrics:
                if metric.name == name:
                    _metrics.append(metric)

        # maximize or minimize
        if fitness.is_max(): isMax = True
        else: isMax = False

        # sort metrics on fitness
        metric = sorted(
            _metrics,
            key = lambda it: it.value,
            reverse = isMax)[0]

        return metric

    ''' serialize '''
    def save(self):

        path = self.path

        result = {
            'id': self.id,
            'metrics': self.metrics,
            'fittest': self.fittest
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



