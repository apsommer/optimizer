import os
import pickle

from tqdm import tqdm

from analysis.Engine import Engine
from utils.EngineUtils import *
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, id, data, path):

        self.id = id
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

        self.fastMomentumMinutes = np.arange(60, 140, 20)
        self.takeProfitPercent = np.arange(.25, .65, .2)
        self.slowMinutes = np.arange(1555, 2655, 200)

    def run(self):

        data = self.data
        params = self.params

        id = 0
        total = (
            len(self.fastMomentumMinutes) *
            len(self.takeProfitPercent) *
            len(self.slowMinutes))

        with tqdm(
            # disable = True,
            total = total,
            colour = 'BLUE',
            bar_format = '{percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            for fastMomentumMinutes in self.fastMomentumMinutes:
                for takeProfitPercent in self.takeProfitPercent:
                    for slowMinutes in self.slowMinutes:

                        if id > 2:
                            break

                        # update params
                        params.fastMomentumMinutes = fastMomentumMinutes
                        params.takeProfitPercent = takeProfitPercent
                        params.slowMinutes = slowMinutes

                        # create strategy and engine
                        strategy = LiveStrategy(data, params)
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

        self.metrics = (
            get_analyzer_metrics(self) +
            get_max_metric(self, 'profit') +
            get_max_metric(self, 'expectancy') +
            get_max_metric(self, 'win_rate') +
            get_max_metric(self, 'average_win') +
            get_min_metric(self, 'average_loss') +
            get_min_metric(self, 'max_drawdown') +
            get_min_metric(self, 'drawdown_per_profit'))

        # todo fitness function cases
        max_profit = get_max_metric(self, 'profit')[0]

        # persist best params
        self.params = load_result(max_profit.id, self.path)['params']
        print(f'\t*[{max_profit.id}]: {self.params}\n')

    def rebuild_engine(self, id):

        data = self.data

        result = load_result(id, self.path)
        params = result['params']

        strategy = LiveStrategy(data, params)

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

