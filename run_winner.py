import time
import warnings

from genetic.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils.utils import *

''' run winner from genetic analysis '''
# INPUT ###########################################################

num_months = 20
id = '20250721_230859'

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
genetic = unpack(id, parent_path)
params = genetic['winner']['params']

# init strategy and engine
id = genetic['winner']['id']
strategy = LiveStrategy(data, emas, fractals, params)
engine = Engine(id, strategy)
engine.run()

# display results
engine.print_metrics()
engine.print_trades(show_last = 1000)
engine.plot_trades()
engine.plot_equity()

