import time

from data import DataUtils as repo
from Engine import *
from PlotUtils import *
from strategy.LiveStrategy import *
from strategy.LiveParams import *

os.system('clear')
start_time = time.time()

# get ohlc prices
csv_filename = 'data/nq_1mon.csv' # 1 month
# csv_filename = "data/nq_3mon.csv"  # 3 months
# csv_filename = "data/nq_6mon.csv"  # 6 months
# csv_filename = "data/nq_24mon.csv" # 2 years

data = repo.getOhlc(csv_filename = csv_filename) # local
#data = repo.getOhlc() # network

# init
params = LiveParams(
    fastMinutes = 25,
    disableEntryMinutes = 120,
    fastMomentumMinutes = 75,
    fastCrossoverPercent = 50,
    takeProfitPercent = 0.5,
    fastAngleFactor = 15,
    slowMinutes = 2355,
    slowAngleFactor = 20,
    coolOffMinutes = 5,
    positionEntryMinutes = 1)
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
print_tv_trades(engine)
# plot_equity(engine)
plot_trades(engine)
