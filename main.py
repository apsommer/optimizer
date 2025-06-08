import os
import time

from analysis.Analyzer import Analyzer
from analysis.Engine import Engine
from analysis.EngineUtils import print_metrics, get_max_metric
from analysis.PlotUtils import *
from data import DataUtils as repo
from strategy.LiveStrategy import LiveStrategy

os.system('clear')
start_time = time.time()

# get ohlc prices
csv_filename = 'data/nq_1mon.csv'
data = repo.getOhlc(csv_filename = csv_filename) # local
# data = repo.getOhlc() # network

percent = 20
runs = 3

IS_len = int(len(data) / ((percent / 100) * runs + 1))
OS_len = int((percent / 100) * IS_len)

IS_start, IS_end = 0, IS_len
OS_start, OS_end = IS_len, IS_len + OS_len

for run in np.arange(0, runs, 1):

    # isolate training set
    IS = data.iloc[IS_start:IS_end]

    # run exhaustive sweep
    path = 'wfa/NQ/IS' + str(percent) + str(runs) + '/' + str(run) + '/'
    analyzer = Analyzer(IS, path)
    analyzer.run()
    print_metrics(analyzer.metrics)

    # get result with highest profit
    max_profit = get_max_metric(analyzer, 'profit')
    id = max_profit[0].id
    params = analyzer.load_result(id)['params']

    # isolate testing set
    OS = data.iloc[OS_start:OS_end]

    # run strategy blind over OS
    strategy = LiveStrategy(OS, params)
    engine = Engine(id, strategy)
    engine.run()

    path = 'wfa/NQ/OS' + str(percent) + str(runs) + '/'
    engine.save(path)

    # print engine metrics
    print_metrics(engine.metrics)

    # slide window forward
    IS_start += OS_len
    IS_end += OS_len
    OS_start += OS_len
    OS_end += OS_len

# print_metrics(engine.metrics)
# engine.print_trades()
# engine = analyzer.rebuild_engine(id)
# plot_equity(engine)
# plot_strategy(engine)

end_time = time.time()
print(f'\nElapsed time: {round(end_time - start_time)} seconds')