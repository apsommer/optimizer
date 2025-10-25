import time
import warnings

from analysis.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import print_metrics
from utils.utils import *

''' run winner from genetic analysis '''
# INPUT ###########################################################

# data, indicators
asset = 'MNG'
num_months = 20
id = '20251024_230257'
engine = None # 'g4e70' # None

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
np.set_printoptions(threshold = 3)
start_time = time.time()

# organize outputs
data_name = asset + '_' + str(num_months) + 'm'
data_path = 'data/' + data_name
parent_path = 'genetic/' + data_name
path = parent_path + '/' + id

# init data and indicators
data = getOhlc(asset, num_months)
emas = unpack('emas', data_path)
fractals = unpack('fractals', data_path)

# unpack analysis
genetic = unpack('analysis', path)
metrics = genetic['metrics']
best_engines = genetic['best_engines']

# display analysis metrics
print_metrics(metrics)

# unpack winning solution
winner_metric = max(best_engines, key = lambda it: it.value)
winner_generation = best_engines.index(winner_metric)
winner_id = 'g' + str(winner_generation) + 'e' + str(winner_metric.id)
if engine is not None: winner_id = engine

# unpack winning solution
winner = unpack(winner_id, path)
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
    engine = unpack(id, path)

    fplt.plot(
        engine['cash_series'],
        color = colors[generation],
        width = 2,
        ax = ax)

    # format legend
    legend = '<span style="font-size:16pt">' + id + '</span>'
    fplt.legend_text_color = colors[generation]
    fplt.add_legend(legend, ax)

fplt.show()