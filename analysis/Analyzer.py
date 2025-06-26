import os
import pickle

import pandas as pd
import pandas.core.util.hashing
from numpy import linspace
from tqdm import tqdm

from analysis.Engine import Engine
from model.Fitness import Fitness
from strategy.FastParams import FastParams
from strategy.FastStrategy import FastStrategy
from utils import utils
from utils.utils import *
from utils.metrics import *
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, id, data, emas, slopes, fractals, opt, wfa_path):

        self.id = id
        self.data = data
        self.emas = emas
        self.slopes = slopes
        self.fractals = fractals
        self.opt = opt
        self.wfa_path = wfa_path
        self.path = wfa_path  + '/' + str(id) + '/'
        self.engines = []
        self.metrics = []
        self.fittest = { }

        # common
        self.params = FastParams(
            takeProfitPercent = None,
            stopLossRatio= None,
            slowAngleFactor = None,
            stopAverage = None,
        )

        # extract opt
        self.takeProfitPercent = self.opt['takeProfitPercent']
        self.stopLossRatio = self.opt['stopLossRatio']
        self.slowAngleFactor = self.opt['slowAngleFactor']
        self.stopAverage = self.opt['stopAverage']

    def run(self):

        params = self.params
        id = 0
        total = (
            len(self.takeProfitPercent)
            * len(self.stopLossRatio)
            * len(self.slowAngleFactor)
            * len(self.stopAverage)
        )

        with tqdm(
            disable = self.id != 0, # show only 1 core
            total = total,
            colour = blue,
            bar_format = '        In-sample:      {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            # sweep params from opt
            for takeProfitPercent in self.takeProfitPercent:
                for stopLossRatio in self.stopLossRatio:
                    for slowAngleFactor in self.slowAngleFactor:
                        for stopAverage in self.stopAverage:

                            # update params
                            params.takeProfitPercent = takeProfitPercent
                            params.stopLossRatio = stopLossRatio
                            params.slowAngleFactor = slowAngleFactor
                            params.stopAverage = stopAverage

                            # create strategy and engine
                            strategy = FastStrategy(self.data, self.emas, self.slopes, self.fractals, params)
                            engine = Engine(id, strategy)

                            # run and save
                            engine.run()
                            engine.save(self.path, False)
                            id += 1

                            pbar.update()

        pbar.close()
        self.analyze()

    def analyze(self):

        # get num of files in dir
        num_engines = len(os.listdir(self.path))
        ids = np.arange(0, num_engines, 1)

        # collect engine metrics
        for id in ids:
            self.engines.append(
                unpack(id, self.path)['metrics'])

        # init metrics
        self.metrics = get_analyzer_metrics(self)

        # persist fittest engines
        for fitness in Fitness:
            metric = self.get_fittest_metric(fitness)
            self.metrics.append(metric)
            self.fittest[fitness] = metric

    def get_fittest_metric(self, fitness):

        engines = self.engines
        fitness_name = fitness.value

        # isolate metric of interest
        _metrics = []
        for metrics in engines:
            for metric in metrics:
                if metric.name == fitness_name:
                    _metrics.append(metric)

        # sort by value
        _sorted = sorted(
            _metrics,
            key = lambda it: it.value,
            reverse = True)

        # tag title
        metric = _sorted[0]
        metric.title = f'[{metric.id}] {metric.title}'
        return metric

    def save(self):

        save(
            bundle = {
                'id': self.id,
                'metrics': self.metrics,
                'fittest': self.fittest,
            },
            filename = 'analyzer',
            path = self.path)
