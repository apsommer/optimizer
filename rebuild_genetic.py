import time
import warnings

from analysis.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import print_metrics
from utils.utils import *

''' run winner from genetic analysis '''
# INPUT ###########################################################

num_months = 12
id = '20250724_164924'

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
np.set_printoptions(threshold = 3)
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
parent_path = 'genetic/' + data_name
analysis_path = parent_path + '/' + id

# get ohlc data and indicators
data = getOhlc(num_months, False)
emas = unpack('emas', parent_path)
fractals = unpack('fractals', parent_path)

# unpack analysis
genetic = unpack('analysis', analysis_path)
metrics = genetic['metrics']
best_engines = genetic['best_engines']

# display analysis metrics
print_metrics(metrics)

# unpack winning solution
winner_metric = max(best_engines, key = lambda it: it.value)
winner_generation = best_engines.index(winner_metric)
winner_id = 'g' + str(winner_generation) + 'e' + str(winner_metric.id)
winner = unpack(winner_id, analysis_path)
params = winner['params']
cash_series = winner['cash_series']
trades = winner['trades']

# build winning engine, but don't run!
strategy = LiveStrategy(data, emas, fractals, params)
engine = Engine(winner_id, strategy)
engine.cash_series = cash_series
engine.trades = trades
engine.analyze()

# display winner
engine.print_metrics()
engine.print_trades()
engine.plot_trades()
ax = engine.plot_equity(shouldShow = False)

# plot equity of best engines
for generation, metric in enumerate(best_engines):

    # unpack full results
    id = 'g' + str(generation) + 'e' + str(metric.id)
    engine = unpack(id, analysis_path)

    fplt.plot(
        engine['cash_series'],
        color = colors[generation],
        width = 2,
        legend = id, # todo clean up legend style
        ax = ax)

fplt.show()