import pandas as pd

from analysis.Analyzer import Analyzer, load_result
from analysis.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils.EngineUtils import print_metrics, get_max_metric

''' required top-level for multiprocessing '''
class WalkForward():

    def __init__(self, num_months, percent, runs, data):
        self.num_months = num_months
        self.percent = percent
        self.runs = runs
        self.data = data

        # organize outputs
        data_name = 'NQ_' + str(num_months) + 'mon'
        self.path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'

        # isolate training and testing sets
        self.IS_len = int(len(data) / ((percent / 100) * runs + 1))
        self.OS_len = int((percent / 100) * self.IS_len)

    def walk_forward(self, run):

        # sweep in-sample
        params = self.sweep_IS(run)

        # last run skip out-of-sample, it is suggested params
        if run == self.runs: return

        # run out-of-sample
        self.run_OS(run, params)

    def sweep_IS(self, run):

        path = self.path + str(run) + '/'

        IS_len = self.IS_len
        OS_len = self.OS_len
        data = self.data

        # isolate training xet
        IS_start = run * OS_len
        IS_end = IS_start + IS_len
        IS = data.iloc[IS_start : IS_end]

        # run exhaustive sweep over IS
        analyzer = Analyzer(run, IS, path)
        analyzer.run()
        # todo analyzer.save()

        # print results
        print_metrics(analyzer.metrics)

        # get result with highest profit
        # todo fitness function cases
        max_profit = get_max_metric(analyzer, 'profit')
        max_profit_id = max_profit[0].id
        params = load_result(max_profit_id, analyzer.path)['params']

        print(f'\t*[{max_profit_id}]\n')
        return params

    def run_OS(self, run, params):

        IS_len = self.IS_len
        OS_len = self.OS_len
        data = self.data

        IS_start = run * OS_len
        IS_end = IS_start + IS_len

        OS_start = IS_end
        OS_end = OS_start + OS_len
        OS = data.iloc[OS_start:OS_end]

        # run strategy blind over OS with best params
        strategy = LiveStrategy(OS, params)
        engine = Engine(run, strategy)
        engine.run()
        engine.save(self.path)

        # print results
        # print_metrics(engine.metrics)
        # engine.print_trades()

    def build_composite(self):

        runs = self.runs
        path = self.path
        data = self.data

        # build composite engine
        equity = pd.Series()
        trades = []
        for run in range(runs):
            equity = equity._append(
                load_result(run, path)['cash_series'])
            trades.extend(
                load_result(run, path)['trades'])

        # mask data to OS sample
        OS = data.loc[equity.index, :]

        # todo get params from last IS
        params = load_result(0, path)['params']

        # create engine, but don't run!
        strategy = LiveStrategy(OS, params)
        engine = Engine('composite', strategy)

        # finish engine build
        engine.cash_series = equity
        engine.trades = trades
        engine.analyze()

        return engine