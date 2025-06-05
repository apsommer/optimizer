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
for fastMomentumMinutes in _fastMomentumMinutes:
    for takeProfitPercent in _takeProfitPercent:
        for slowMinutes in _slowMinutes:

            # todo temp
            if id > 2: break

            # update params
            params.fastMomentumMinutes = fastMomentumMinutes
            params.takeProfitPercent = takeProfitPercent
            params.slowMinutes = slowMinutes

            # create strategy and engine
            strategy = LiveStrategy(data, params)
            engine = Engine(id=id, strategy=strategy)

            # run and save
            engine.run()
            engine.save()
            id += 1

for id in np.arange(0, 3, 1):

    slim_engine = load_engine(id=id)
    print(f'Engine: {slim_engine['id']}')
    print_metrics(slim_engine['metrics'])
    print(f'Profit: {slim_engine['metrics']['profit'].value}')


########################################################################
end_time = time.time()
print(f'Elapsed time: {round(end_time - start_time)} seconds')

# plot results
print_metrics(engine.metrics)
print_trades(engine)

plot_equity(engine)
plot_strategy(engine)
