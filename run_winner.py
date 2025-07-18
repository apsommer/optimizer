import warnings

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.utils import *

''' run winner from genetic analysis '''
# INPUT ###########################################################

num_months = 28

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
parent_path = 'genetic/' + data_name

# get ohlc data and indicators
data = getOhlc(num_months, False)
emas = unpack('emas', parent_path)
fractals = unpack('fractals', parent_path)

# unpack winner
analysis = unpack('analysis', parent_path)
# params = analysis['winner']['params']
params = analysis['params']

# init strategy and engine
# id = analysis['winner']['id']
id = analysis['id']
strategy = LiveStrategy(data, emas, fractals, params)
engine = Engine(id, strategy)

# display results
engine.run()
engine.print_metrics()
engine.print_trades()
engine.plot_trades()
engine.plot_equity()

