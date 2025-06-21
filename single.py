import os
import time
import warnings

from strategy.LiveParams import LiveParams
from utils.constants import *
from utils.plots import *
from utils.utils import *

''' examine single engine '''

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

path = 'wfa/NQ_3mon/20_14'
data = getOhlc(14, False)
create_indicators(data, path)
indicators = unpack('indicators', path)

params = LiveParams(
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
    id = 42,
    strategy = strategy)

engine.run()

fplt.plot(
    engine.cash_series,
    ax = init_plot(engine.id))

fplt.show()


