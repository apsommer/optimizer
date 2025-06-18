import os
import pickle

import pandas as pd
from numpy import linspace
from tqdm import tqdm

from analysis.Engine import Engine
from model.Fitness import Fitness
from utils import utils
from utils.utils import *
from utils.metrics import *
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, id, data, opt, path):

        self.id = id
        self.data = data
        self.opt = opt
        self.path = path + str(id) + '/'
        self.wfa_path = path

        self.results = []
        self.metrics = []
        self.fittest = { }

        self.avgs = load_result('avgs', self.wfa_path)

        # common
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

        # extract opt
        self.disableEntryMinutes = self.opt['disableEntryMinutes']
        self.fastMomentumMinutes = self.opt['fastMomentumMinutes']
        self.takeProfitPercent = self.opt['takeProfitPercent']

    def run(self):

        params = self.params

        id = 0
        total = len(self.disableEntryMinutes) * len(self.fastMomentumMinutes) * len(self.takeProfitPercent)

        with tqdm(
            disable = self.id != 0,
            # leave = self.id == 0,
            # position = self.id,
            total = total,
            colour = '#4287f5',
            bar_format = '        In-sample:      {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

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
                        strategy = LiveStrategy(self.data, self.avgs, params)
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
            result = load_result(id, self.path)
            metrics = result['metrics']
            self.results.append(metrics)

        # init metrics
        self.metrics = get_analyzer_metrics(self)

        # persist fittest engines
        for fitness in Fitness:
            metric = self.get_fittest_metric(fitness)
            self.metrics.append(metric)
            self.fittest[fitness] = metric

    def get_fittest_metric(self, fitness):

        results = self.results
        name = fitness.value

        # isolate metric of interest
        _metrics = []
        for metrics in results:
            for metric in metrics:
                if metric.name == name:
                    _metrics.append(metric)

        # sort metrics on fitness
        ranked = sorted(
            _metrics,
            key = lambda it: it.value,
            reverse = fitness.is_max)

        metric = ranked[0]

        # tag title
        title = '* ' + metric.title

        return Metric(metric.name, metric.value, metric.unit, title, metric.formatter, metric.id)

    ''' serialize ''' # todo extract common save()
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



