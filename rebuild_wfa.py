import time
import warnings

from analysis.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import print_metrics, print_composite_summary
from utils.utils import *

''' display results of walk forward analysis '''
# INPUT ###########################################################

# data, indicators
asset = 'GC'
num_months = 20
percent = 25
runs = 9 # +1 added for final in-sample
id = '20250917_083033'

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
np.set_printoptions(threshold = 3)
start_time = time.time()

# organize outputs
data_name = asset + '_' + str(num_months) + 'm'
data_path = 'data/' + data_name
parent_path = 'wfa/' + data_name
path = parent_path + '/' + id

# init data and indicators
data = getOhlc(asset, num_months)
emas = unpack('emas', data_path)
fractals = unpack('fractals', data_path)

# unpack analysis
wfa = unpack(id, path)
metrics = wfa['metrics']
composite_summary = wfa['composite_summary']
winner_id = wfa['winner_id']

# display analysis metrics
print_metrics(metrics)
print_composite_summary(composite_summary)

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
ax = engine.plot_equity()
