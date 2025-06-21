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

# data
num_months = 3
isNetwork = False

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

data = getOhlc(num_months, isNetwork)

path = 'wfa/single'
create_avgs(data, path)
avgs = unpack('avgs', path)

params = FastParams(
    fastMinutes = 25,
    fastCrossoverPercent = 0,
    takeProfitPercent = 0.45,
    fastAngleFactor = 25,
    slowMinutes = 2555,
    slowAngleFactor = 20,
    coolOffMinutes = 5,
    ratio= 2)

strategy = FastStrategy(
    data = data,
    avgs= avgs,
    params = params)

engine = Engine(
    id = 0,
    strategy = strategy)

engine.run(
    showProgress = True)

# engine.print_metrics()
# engine.print_trades()
# engine.plot_trades()
# engine.plot_equity()

strategy.plot()


