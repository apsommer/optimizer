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

# todo isolate training set
ratio = 0.8
sep = int(ratio * len(data))
IS = data[:sep] # in-sample
OS = data[sep:] # out-of-sample

# run IS exhaustive sweep
analyzer = Analyzer(IS, 'wfa/NQ/IS80')
analyzer.run()
print_metrics(analyzer.metrics)
# engine = analyzer.rebuild_engine(id)

# get IS run with highes profit
id = get_max_metric(analyzer, 'profit')[0].id
params = analyzer.load_result(id)['params']

# run OS single configuration with best IS params
strategy = LiveStrategy(OS, params)
engine = Engine(id, strategy)
engine.run()
engine.save('wfa/NQ/OS20')

# print engine metrics
print_metrics(engine.metrics)
engine.print_trades()

# plot strategy and equity
plot_equity(engine)
plot_strategy(engine)

end_time = time.time()
print(f'\nElapsed time: {round(end_time - start_time)} seconds')