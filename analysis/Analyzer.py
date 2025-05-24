import time

from data import DataUtils as repo
from Engine import *
from PlotUtils import *
from strategy.LiveStrategy import *
from strategy.LiveParams import *

# config
start_time = time.time()

# get ohlc prices
csv_filename = "data/nq_3months_2025-02-01_2025-05-01.csv"  # 3 months
# csv_filename = "data/nq_2years_2023-03-15_2025-03-15.csv" # 2 years

data = repo.getOhlc(csv_filename = csv_filename) # local
# data = repo.getOhlc() # network

# init
params = LiveParams(
    fastMinutes = 25,
    disableEntryMinutes = 105,
    fastMomentumMinutes = 135,
    fastCrossoverPercent = 90,
    takeProfitPercent = 0.35,
    fastAngleFactor = 15,
    slowMinutes = 2355,
    slowAngleFactor = 20)
strategy = LiveStrategy(data, params)
engine = Engine(strategy)
# engine = load_engine(0, 'output', strategy)

# run
engine.run()
engine.save(0, 'output')

########################################################################
end_time = time.time()
print(f'Elapsed time: {round(end_time - start_time, 2)} seconds')

# plot results
print_metrics(engine)
plot_equity(engine)
plot_trades(engine)
