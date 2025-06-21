import os
import time
import warnings

from strategy.FastParams import FastParams
from strategy.LiveParams import LiveParams
from utils.constants import *
from utils.plots import *
from utils.utils import *

''' examine single engine '''

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

num_months = 3
data = getOhlc(num_months, False)

path = 'wfa/single'
create_indicators(data, path)
indicators = unpack('indicators', path)

params = FastParams(
    fastMinutes = 25,
    fastCrossoverPercent = 0,
    takeProfitPercent = 0.45,
    fastAngleFactor = 25,
    slowMinutes = 2555,
    slowAngleFactor = 20,
    coolOffMinutes = 5,
    timeout = 2)

strategy = FastStrategy(
    data = data,
    indicators = indicators,
    params = params)

engine = Engine(
    id = 0,
    strategy = strategy)

print('running ...')
engine.run()

print('plotting ...')
plot_equity(engine)



