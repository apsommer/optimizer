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
#csv_filename = "data/nq_24mon.csv" # 2 years

data = repo.getOhlc(csv_filename = csv_filename) # local
# data = repo.getOhlc() # network

_fastMomentumMinutes = np.arange(55, 95, 5) # np.arange(55, 140, 5)
_takeProfitPercent = np.arange(0.25, 0.55, 0.05) # np.arange(0.25, 0.80, .05)
_slowMinutes = np.arange(1555, 1855, 100) # np.arange(1555, 2655, 100)

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

id = 0
for i, fastMomentumMinutes in enumerate(_fastMomentumMinutes):
    for j, takeProfitPercent in enumerate(_takeProfitPercent):
        for k, slowMinutes in enumerate(_slowMinutes):

            # update params
            params.fastMomentumMinutes = fastMomentumMinutes
            params.takeProfitPercent = takeProfitPercent
            params.slowMinutes = slowMinutes

            # create strategy, engine
            strategy = LiveStrategy(data, params)
            engine = Engine(strategy)

            # run and save
            print(id)
            engine.run()
            engine.save(id, 'output')
            id += 1

########################################################################
end_time = time.time()
print(f'Elapsed time: {round(end_time - start_time)} seconds')

# plot results
print_metrics(engine)
print_trades(engine)

plot_equity(engine)
plot_strategy(engine)
