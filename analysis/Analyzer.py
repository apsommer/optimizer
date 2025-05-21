import matplotlib.pyplot as plt
from data import DataUtils as repo
from Engine import Engine, print_stats
from strategy.HalfwayStrategy import HalfwayStrategy
import logging

# config
plt.rcParams['figure.figsize'] = [20, 12]
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

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
results = engine.run()

# print results to console
print_stats(results)
# engine.print_trades()

# plot results
engine.plot_strategy()
engine.plot_trades()