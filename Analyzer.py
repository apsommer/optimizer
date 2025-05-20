import matplotlib.pyplot as plt
import Repository as repo
from Engine import Engine, print_stats
from HalfwayStrategy import HalfwayStrategy
import logging

# config
plt.rcParams['figure.figsize'] = [20, 12]
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# get ohlc prices
csv_filename = "data/nq_3months_2025-02-01_2025-05-01.csv"
data = repo.getOhlc(csv_filename = csv_filename) # local
# data = repo.getOhlc() # network


# init engine
strategy = HalfwayStrategy()
engine = Engine(initial_cash = 1000)
engine.strategy = strategy
engine.data = data

# run engine
stats = engine.run()

# plot results
print_stats(stats)
# engine.print_trades()
engine.plot()
