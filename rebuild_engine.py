
import warnings
from analysis.Engine import Engine
from common import init_engine
from strategy.FastParams import FastParams
from strategy.FastStrategy import FastStrategy
from utils.utils import *

''' rebuild single engine '''
# INPUT ###########################################################

# data, indicators
num_months = 8
isNetwork = False
path = 'wfa/NQ_8mon'

# finished engine
engine_path = path + '/20_14'
id = 'win_rate'

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

engine = init_engine(
    num_months = num_months,
    isNetwork = isNetwork,
    path = path)

# unpack bin
bin = unpack(id, engine_path)
engine.id = bin['id']
engine.params = bin['params']
engine.metrics = bin['metrics']
engine.trades = bin['trades']
engine.cash_series = bin['cash_series']

# print results
engine.print_metrics()
engine.print_trades()
engine.plot_trades()
engine.plot()
