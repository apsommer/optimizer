import os

from analysis.Engine import Engine
from analysis.EngineUtils import load_engine
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, data, params):

        self.data = data
        self.params = params
        self.metrics = None

    def run(self):

        data = self.data
        params = self.params

        # todo move?
        _fastMomentumMinutes = np.arange(55, 95, 5)  # np.arange(55, 140, 5)
        _takeProfitPercent = np.arange(0.25, 0.55, 0.05)  # np.arange(0.25, 0.80, .05)
        _slowMinutes = np.arange(1555, 1855, 100)  # np.arange(1555, 2655, 100)

        id = 0
        for fastMomentumMinutes in _fastMomentumMinutes:
            for takeProfitPercent in _takeProfitPercent:
                for slowMinutes in _slowMinutes:

                    # todo temp
                    if id > 2: break

                    # update params
                    params.fastMomentumMinutes = fastMomentumMinutes
                    params.takeProfitPercent = takeProfitPercent
                    params.slowMinutes = slowMinutes

                    # create strategy and engine
                    strategy = LiveStrategy(data, params)
                    engine = Engine(id=id, strategy=strategy)

                    # run and save
                    engine.run()
                    engine.save()
                    id += 1

        self.analyze()

    def analyze(self, dir='output'):

        #
        num_engines = len(os.listdir(dir))
        ids = np.arange(0, num_engines-1, 1)

        for id in ids:

            slim_engine = load_engine(id=id)
            print(f'Engine: {slim_engine['id']}')
            print(f'Profit: {slim_engine['metrics']['profit'].value}')

            # # maximum
            # max_profit = np.max()
            #
            # metrics = [
            #     Metric('win_rate', win_rate, '%', 'Win rate')]

