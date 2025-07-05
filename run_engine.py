import os
import time
import warnings

from analysis.Engine import Engine
from common import init_engine
from strategy.FastParams import FastParams
from strategy.FastStrategy import FastStrategy
from utils.constants import *
from utils.metrics import *
from utils.utils import *

''' run single engine '''
# INPUT ###########################################################

# data, indicators
num_months = 10
isNetwork = False
path = 'wfa/single'

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

engine = init_engine(
    num_months = num_months,
    isNetwork = isNetwork,
    path = path)

engine.run()
engine.save(
    path = path,
    isFull = True)

engine.print_metrics()
engine.print_trades()
engine.plot_trades()
engine.plot_equity()

