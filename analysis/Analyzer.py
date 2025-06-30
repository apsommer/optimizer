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

        # extract opt
        self.fastMinutes = self.opt.fastMinutes
        self.disableEntryMinutes = self.opt.disableEntryMinutes
        self.fastMomentumMinutes = self.opt.fastMomentumMinutes
        self.fastCrossoverPercent = self.opt.fastCrossoverPercent
        self.takeProfitPercent = self.opt.takeProfitPercent
        self.fastAngleFactor = self.opt.fastAngleFactor
        self.slowMinutes = self.opt.slowMinutes
        self.slowAngleFactor = self.opt.slowAngleFactor
        self.coolOffMinutes = self.opt.coolOffMinutes
        self.trendStartHour = self.opt.trendStartHour
        self.trendEndHour = self.opt.trendEndHour

    def run(self):

        id = 0
        with tqdm(
            disable = self.id != 0, # show only 1 core
            total = self.opt.size,
            colour = blue,
            bar_format = '        In-sample:      {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            # sweep params from opt
            for fastMinutes in self.fastMinutes:
                for disableEntryMinutes in self.disableEntryMinutes:
                    for fastMomentumMinutes in self.fastMomentumMinutes:
                        for fastCrossoverPercent in self.fastCrossoverPercent:
                            for takeProfitPercent in self.takeProfitPercent:
                                for fastAngleFactor in self.fastAngleFactor:
                                    for slowMinutes in self.slowMinutes:
                                        for slowAngleFactor in self.slowAngleFactor:
                                            for coolOffMinutes in self.coolOffMinutes:
                                                for trendStartHour in self.trendStartHour:
                                                    for trendEndHour in self.trendEndHour:

                                                        # update params
                                                        params = LiveParams(
                                                            fastMinutes = fastMinutes,
                                                            disableEntryMinutes = disableEntryMinutes,
                                                            fastMomentumMinutes = fastMomentumMinutes,
                                                            fastCrossoverPercent = fastCrossoverPercent,
                                                            takeProfitPercent = takeProfitPercent,
                                                            fastAngleFactor = fastAngleFactor,
                                                            slowMinutes = slowMinutes,
                                                            slowAngleFactor = slowAngleFactor,
                                                            coolOffMinutes = coolOffMinutes,
                                                            trendStartHour = trendStartHour,
                                                            trendEndHour = trendEndHour,
                                                        )

                                                        # create strategy and engine
                                                        strategy = LiveStrategy(self.data, self.emas, self.slopes, self.fractals, params)
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

            engine_metrics = unpack(id, self.path)['metrics']
            self.engines.append(engine_metrics)

        # init metrics
        self.metrics = get_analyzer_metrics(self)

        # persist fittest engines
        for fitness in Fitness:

            metric = self.get_fittest_metric(fitness)

            if metric is None: continue

            self.metrics.append(metric)
            self.fittest[fitness] = metric

    def get_fittest_metric(self, fitness):

        engines = self.engines

        # isolate metric of interest
        _metrics = []
        for metrics in engines:
            for metric in metrics:
                if metric.name == fitness.value:
                    _metrics.append(metric)

        # sort by value
        _sorted = sorted(
            _metrics,
            key = lambda it: it.value,
            reverse = True)

        # find first profitable engine for this fitness
        for metric in _sorted:

            id = metric.id
            engine_metrics = unpack(id, self.path)['metrics']
            profit = next((metric.value for metric in engine_metrics if metric.name == 'profit'), None)

            if profit > 0:
                metric.title = f'[{metric.id}] {metric.title}' # tag title
                return metric

        return None

    def save(self):

        save(
            bundle = {
                'id': self.id,
                'metrics': self.metrics,
                'fittest': self.fittest,
            },
            filename = 'analyzer',
            path = self.path)
