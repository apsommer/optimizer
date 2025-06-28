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
from strategy.LiveParams import LiveParams
from utils import utils
from utils.utils import *
from utils.metrics import *
from strategy.LiveStrategy import *

class LiveAnalyzer:

    def __init__(self, id, data, emas, slopes, opt, wfa_path):

        self.id = id
        self.data = data
        self.emas = emas
        self.slopes = slopes
        self.opt = opt
        self.wfa_path = wfa_path
        self.path = wfa_path  + '/' + str(id) + '/'
        self.engines = []
        self.metrics = []
        self.fittest = { }

        # common
        self.params = LiveParams(
            fastMinutes=opt.fastMinutes,
            disableEntryMinutes=None,
            fastMomentumMinutes=None,
            fastCrossoverPercent=opt.fastCrossoverPercent,
            takeProfitPercent=None,
            fastAngleFactor=opt.fastAngleFactor,
            slowMinutes=opt.slowMinutes,
            slowAngleFactor=None,
            coolOffMinutes=opt.coolOffMinutes,
        )

        # extract opt
        self.disableEntryMinutes = self.opt.disableEntryMinutes
        self.fastMomentumMinutes = self.opt.fastMomentumMinutes
        self.takeProfitPercent = self.opt.takeProfitPercent
        self.slowAngleFactor = self.opt.slowAngleFactor

    def run(self):

        params = self.params
        id = 0
        total = (
            len(self.disableEntryMinutes)
            * len(self.fastMomentumMinutes)
            * len(self.takeProfitPercent)
            * len(self.slowAngleFactor)
        )

        with tqdm(
            disable = self.id != 0, # show only 1 core
            total = total,
            colour = blue,
            bar_format = '        In-sample:      {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            # sweep params from opt
            for disableEntryMinutes in self.disableEntryMinutes:
                for fastMomentumMinutes in self.fastMomentumMinutes:
                    for takeProfitPercent in self.takeProfitPercent:
                        for slowAngleFactor in self.slowAngleFactor:

                            # update params
                            params.disableEntryMinutes = disableEntryMinutes
                            params.fastMomentumMinutes = fastMomentumMinutes
                            params.takeProfitPercent = takeProfitPercent
                            params.slowAngleFactor = slowAngleFactor

                            # create strategy and engine
                            strategy = LiveStrategy(self.data, self.emas, self.slopes, params)
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
