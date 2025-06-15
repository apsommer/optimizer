import os
import pickle

import pandas as pd
from numpy import linspace
from tqdm import tqdm

from analysis.Engine import Engine
from model.Fitness import Fitness
from utils.utils import load_result
from utils.metrics import *
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
            disableEntryMinutes = None,
            fastMomentumMinutes = None,
            fastCrossoverPercent = 0,
            takeProfitPercent = None,
            fastAngleFactor = 15,
            slowMinutes = 2555,
            slowAngleFactor = 20,
            coolOffMinutes = 5)

        num = 5
        self.disableEntryMinutes = linspace(60, 180, num = num, dtype = int)
        self.fastMomentumMinutes = linspace(55, 130, num = num, dtype = int)
        self.takeProfitPercent = linspace(.25, .70, num = num, dtype = float)

    def run(self):

        data = self.data
        params = self.params

        id = 0
        total = len(self.disableEntryMinutes) * len(self.fastMomentumMinutes) * len(self.takeProfitPercent)

        with tqdm(
            # disable = self.id != 0,
            # leave = False,
            total = total,
            colour = '#4287f5',
            bar_format = '      {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            for disableEntryMinutes in self.disableEntryMinutes:
                for fastMomentumMinutes in self.fastMomentumMinutes:
                    for takeProfitPercent in self.takeProfitPercent:

                        # if id > 100:
                        #     break

                        # update params
                        params.disableEntryMinutes = disableEntryMinutes
                        params.fastMomentumMinutes = fastMomentumMinutes
                        params.takeProfitPercent = takeProfitPercent

                        # create strategy and engine
                        strategy = LiveStrategy(data, self.avgs, params)
                        engine = Engine(id, strategy)

                        # run and save
                        engine.run()
                        engine.save(self.path)
                        id += 1

                        pbar.update()

        pbar.close()
        self.analyze()

    def analyze(self):

        # get num of files in dir
        num_engines = len(os.listdir(self.path))
        ids = np.arange(0, num_engines, 1)

        # collect engine metrics
        # for id in tqdm(
        #     iterable = ids,
        #     colour = '#42f5f5',
        #     bar_format = '       {percentage:3.0f}%|{bar:100}{r_bar}'):
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
        if fitness.is_max: isMax = True
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



