import os
import pickle

from analysis.Engine import Engine
from utils.EngineUtils import *
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

def thread_target(engine, path):

    # run and save
    engine.run()
    engine.save(self.path)

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

        self.fastMomentumMinutes = np.arange(55, 140, 5)
        self.takeProfitPercent = np.arange(.25, .65, .05)
        self.slowMinutes = np.arange(1555, 2655, 150)

    def run(self):

        data = self.data
        params = self.params

        id = 0
        for fastMomentumMinutes in self.fastMomentumMinutes:
            for takeProfitPercent in self.takeProfitPercent:
                for slowMinutes in self.slowMinutes:

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
            get_analyzer_metrics(self) +
            get_max_metric(self, 'profit') +
            get_max_metric(self, 'expectancy') +
            get_max_metric(self, 'win_rate') +
            get_max_metric(self, 'average_win') +
            get_min_metric(self, 'average_loss') +
            get_min_metric(self, 'max_drawdown') +
            get_min_metric(self, 'drawdown_per_profit'))

    def rebuild_engine(self, id):

        data = self.data

        result = self.load_result(id)
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

########################################################################################################################

def walk_forward(run, percent, runs, data, path):

    # organize output
    IS_path = path + str(run) + '/'

    # isolate training and testing sets
    IS_len = int(len(data) / ((percent / 100) * runs + 1))
    OS_len = int((percent / 100) * IS_len)

    IS_start = run * OS_len
    IS_end = IS_start + IS_len
    OS_start = IS_end
    OS_end = OS_start + OS_len

    IS = data.iloc[IS_start:IS_end]
    OS = data.iloc[OS_start:OS_end]

    # run exhaustive sweep over IS
    analyzer = Analyzer(run, IS, IS_path)
    analyzer.run()
    print_metrics(analyzer.metrics)

    # get result with highest profit
    max_profit = get_max_metric(analyzer, 'profit')
    max_profit_id = max_profit[0].id
    print(f'\t*[{max_profit_id}]\n')
    params = analyzer.load_result(max_profit_id)['params']

    # run strategy blind over OS with best params
    strategy = LiveStrategy(OS, params)
    engine = Engine(run, strategy)
    engine.run()
    engine.save(path)

    # print engine metrics
    print_metrics(engine.metrics)

    # print_metrics(engine.metrics)
    # engine.print_trades()
    # engine = analyzer.rebuild_engine(id)
    # plot_equity(engine)
    # plot_strategy(engine)