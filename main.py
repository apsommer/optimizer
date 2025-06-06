import os
import time

from analysis.Analyzer import Analyzer
from analysis.Engine import Engine
from analysis.EngineUtils import load_engine
from analysis.PlotUtils import *
from data import DataUtils as repo
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy

os.system('clear')
start_time = time.time()

# get ohlc prices
csv_filename = 'data/nq_1mon.csv' # 1 month
# csv_filename = "data/nq_3mon.csv"  # 3 months
# csv_filename = "data/nq_6mon.csv"  # 6 months
# csv_filename = "data/nq_24mon.csv" # 2 years

data = repo.getOhlc(csv_filename = csv_filename) # local
# data = repo.getOhlc() # network

params = LiveParams(
    fastMinutes = 25,
    disableEntryMinutes = 105,
    fastMomentumMinutes = None,
    fastCrossoverPercent = 0,
    takeProfitPercent = None,
    fastAngleFactor = 15,
    slowMinutes = None,
    slowAngleFactor = 20,
    coolOffMinutes = 5)

analyzer = Analyzer(
    data = data,
    params = params)

# analyzer.run()
analyzer.analyze()

engine = analyzer.rebuild(
    id = 6,
    data = data)

# todo
# engine.print_metrics()
# engine.print_trades()
print_metrics(engine)
print_trades(engine)

plot_equity(engine)
plot_strategy(engine)

end_time = time.time()
print(f'Elapsed time: {round(end_time - start_time)} seconds')