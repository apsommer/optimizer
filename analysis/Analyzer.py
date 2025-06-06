import os
import pickle

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *

class Analyzer:

    def __init__(self, data, path):

        self.data = data
        self.path = path
        self.slims = None
        self.metrics = None

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
        self.takeProfitPercent = np.arange(0.25, 0.80, .05)
        self.slowMinutes = np.arange(1555, 2655, 100)

    def run(self):

        data = self.data
        params = self.params

        id = 0
        for fastMomentumMinutes in self.fastMomentumMinutes:
            for takeProfitPercent in self.takeProfitPercent:
                for slowMinutes in self.slowMinutes:

                    # todo temp
                    if id > 9: break

                    # update params
                    params.fastMomentumMinutes = fastMomentumMinutes
                    params.takeProfitPercent = takeProfitPercent
                    params.slowMinutes = slowMinutes

                    # create strategy and engine
                    strategy = LiveStrategy(data, params)
                    engine = Engine(id=id, strategy=strategy)

                    # run and save
                    engine.run()
                    engine.save(self.path)
                    id += 1

        self.analyze()

    def analyze(self):

        # get num of files in dir
        num_engines = len(os.listdir(self.path))
        ids = np.arange(0, num_engines, 1)

        columns = [
            'profit',
            'max_drawdown',
            'profit_factor',
            'drawdown_per_profit',
            'expectancy',
            'trades_per_day']

        slims = pd.DataFrame(
            index=ids,
            columns=columns)

        for id in ids:

            slim = self.load_engine(id)

            slims.loc[id, 'profit'] = slim['metrics']['profit'].value
            slims.loc[id, 'max_drawdown'] = slim['metrics']['max_drawdown'].value
            slims.loc[id, 'profit_factor'] = slim['metrics']['profit_factor'].value
            slims.loc[id, 'drawdown_per_profit'] = slim['metrics']['drawdown_per_profit'].value
            slims.loc[id, 'expectancy'] = slim['metrics']['expectancy'].value
            slims.loc[id, 'trades_per_day'] = slim['metrics']['trades_per_day'].value

        self.slims = slims

    def print_metrics(self):

        slims = self.slims

        print()

        max_profit = np.max(slims.profit)
        idx = slims[slims.profit == max_profit].index.values[0]
        print(f'max_profit: {round(max_profit)}, e{idx}')

        min_drawdown = np.min(slims.max_drawdown)
        idx = slims[slims.max_drawdown == min_drawdown].index.values[0]
        print(f'min_drawdown: {round(min_drawdown)}, e{idx}')

        max_pf = np.max(slims.profit_factor)
        idx = slims[slims.profit_factor == max_pf].index.values[0]
        print(f'max_pf: {max_pf}, e{idx}')

        min_dpp = np.min(slims.drawdown_per_profit)
        idx = slims[slims.drawdown_per_profit == min_dpp].index.values[0]
        print(f'min_dpp: {round(min_dpp)}, e{idx}')

        max_expectancy = np.max(slims.expectancy)
        idx = slims[slims.expectancy == max_expectancy].index.values[0]
        print(f'max_expectancy: {round(max_expectancy, 2)}, e{idx}')

        min_trades_per_day = np.min(slims.trades_per_day)
        idx = slims[slims.trades_per_day == min_trades_per_day].index.values[0]
        print(f'min_trades_per_days: {round(min_trades_per_day, 2)}, e{idx}')

        print()

    def rebuild(self, id):

        data = self.data
        slim = self.load_engine(id)

        strategy = LiveStrategy(
            data=data,
            params=slim['params'])

        engine = Engine(id, strategy)
        engine.run()

        return engine

    ''' deserialize '''
    def load_engine(self, id):

        filename = 'e' + str(id) + '.bin'
        path_filename = self.path + '/' + filename
        filehandler = open(path_filename, 'rb')
        return pickle.load(filehandler)