import time

from data import DataUtils as repo
from Engine import *
from strategy.HalfwayStrategy import HalfwayStrategy

# config
start_time = time.time()


# get ohlc prices
csv_filename = "data/nq_3months_2025-02-01_2025-05-01.csv"  # 3 months
# csv_filename = "data/nq_2years_2023-03-15_2025-03-15.csv" # 2 years

data = repo.getOhlc(csv_filename = csv_filename) # local
# data = repo.getOhlc() # network

# init
strategy = HalfwayStrategy()
engine = Engine()
engine.strategy = strategy
engine.data = data

# run
engine.run()

########################################################################
end_time = time.time()
print(f'Elapsed time: {round(end_time - start_time, 2)} seconds')

# print results to console
engine.print_metrics()
# engine.print_trades()

# plot results
engine.plot_equity()
engine.plot_trades()
