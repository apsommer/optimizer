import os
import time

from analysis.Analyzer import Analyzer
from analysis.PlotUtils import *
from data import DataUtils as repo

os.system('clear')
start_time = time.time()

# get ohlc prices
csv_filename = 'data/nq_1mon.csv' # 1 month
# csv_filename = "data/nq_3mon.csv"  # 3 months
# csv_filename = "data/nq_6mon.csv"  # 6 months
# csv_filename = "data/nq_24mon.csv" # 2 years

data = repo.getOhlc(csv_filename = csv_filename) # local
# data = repo.getOhlc() # network

analyzer = Analyzer(data, 'wfa/MNQ')
analyzer.run()
analyzer.print_metrics()

# todo hunt for best engine

# rebuild engine of interest
engine = analyzer.rebuild(7)

# print engine metrics
engine.print_metrics()
engine.print_trades()

# plot strategy and equity
plot_equity(engine)
plot_strategy(engine)

end_time = time.time()
print(f'Elapsed time: {round(end_time - start_time)} seconds')