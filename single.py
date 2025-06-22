import os
import time
import warnings

from analysis.Engine import Engine
from strategy.FastParams import FastParams
from strategy.FastStrategy import FastStrategy
from utils.constants import *
from utils.metrics import *
from utils.utils import *

''' examine single engine '''
# INPUT ###########################################################

num_months = 3
isNetwork = False
path = 'wfa/single'

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
    takeProfitPercent = 0.5,
    stopLossPercent = 0.5,)

strategy = FastStrategy(
    data = data,
    emas = emas,
    slopes = slopes,
    fractals = fractals,
    params = params)

engine = Engine(
    id = 'single',
    strategy = strategy)
engine.run(
    showProgress = True)
engine.save(
    path = path,
    isFull = True)

engine.print_metrics()
engine.print_trades()
engine.plot_trades()
engine.plot_equity()

# strategy.plot(
#     show = True)