import os
import pickle

import pandas as pd
import pandas.core.util.hashing
from numpy import linspace
from tqdm import tqdm

from analysis.Engine import Engine
from model.Fitness import Fitness
from strategy.FastStrategy import FastStrategy
from utils import utils
from utils.utils import *
from utils.metrics import *
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, id, data, opt, wfa_path):

        self.id = id
        self.data = data
        self.opt = opt
        self.wfa_path = wfa_path
        self.path = wfa_path  + '/' + str(id) + '/'
        self.engines = []
        self.metrics = []
        self.fittest = { }

        # indicators for each process (core)
        self.indicators = unpack('indicators', self.wfa_path)

        # common
        self.params = LiveParams(
            fastMinutes = 25,
            fastCrossoverPercent = 0,
            takeProfitPercent = None,
            fastAngleFactor = None,
            slowMinutes = 2555,
            slowAngleFactor = 20,
            coolOffMinutes = 5,
            timeout = None)

        # extract opt
        self.takeProfitPercent = self.opt['takeProfitPercent']
        self.fastAngleFactor = self.opt['fastAngleFactor']
        self.timeout = self.opt['timeout']

    def run(self):

        params = self.params
        id = 0
        total = len(self.takeProfitPercent) * len(self.fastAngleFactor) * len(self.timeout)

        with tqdm(
            disable = self.id != 0, # show only 1 core
            total = total,
            colour = '#4287f5',
            bar_format = '        In-sample:      {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            # sweep params from opt
            for takeProfitPercent in self.takeProfitPercent:
                for fastAngleFactor in self.fastAngleFactor:
                    for timeout in self.timeout:

                        # update params
                        params.takeProfitPercent = takeProfitPercent
                        params.fastAngleFactor = fastAngleFactor
                        params.timeout = timeout

                        # create strategy and engine
                        # strategy = LiveStrategy(self.data, self.indicators, params)
                        strategy = FastStrategy(self.data, self.indicators, params)
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

        # sort based on fitness max/min
        isReversed = fitness.is_max

        metric = sorted(
            _metrics,
            key = lambda it: it.value,
            reverse = isReversed)[0]

        # tag title
        metric.title = '* ' + metric.title
        return metric

    def save(self):

        bundle = {
            'id': self.id,
            'metrics': self.metrics,
            'fittest': self.fittest
        }

        save(
            bundle = bundle,
            filename = 'analyzer',
            path = self.path
        )
