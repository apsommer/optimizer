
import warnings
from analysis.Engine import Engine
from strategy.FastParams import FastParams
from strategy.FastStrategy import FastStrategy
from utils.utils import *

''' rebuild single engine '''
# INPUT ###########################################################

num_months = 3
isNetwork = False
path = 'wfa/NQ_3mon'
engine_path = path + '/20_14'
id = 'drawdown'

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

data = getOhlc(num_months, isNetwork)

# build_indicators(data, path)
emas = unpack('emas', path)
slopes = unpack('slopes', path)
fractals = unpack('fractals', path)

params = FastParams(
    takeProfitPercent = np.nan,
    stopLossPercent = np.nan,
    proximityPercent = np.nan)

strategy = FastStrategy(
    data = data,
    emas = emas,
    slopes = slopes,
    fractals = fractals,
    params = params)

engine = Engine(
    id = 'single',
    strategy = strategy)

# don't run or save!

# copy from bin to engine
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
engine.plot_equity()
