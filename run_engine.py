import warnings

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.utils import *

''' run single engine '''
# INPUT ###########################################################

# data, indicators
num_months = 6
isNetwork = False
path = 'wfa/single'

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

data = getOhlc(num_months, isNetwork)

# build_indicators(data, path)
emas = unpack('emas', path)
fractals = unpack('fractals', path)

params = LiveParams(
    fastMinutes=25,
    disableEntryMinutes=0,
    fastMomentumMinutes=105,
    fastCrossoverPercent=0,
    takeProfitPercent=.5,
    fastAngleFactor=0,
    slowMinutes=5555,
    slowAngleFactor=15,
    coolOffMinutes=5,
    trendStartHour=12,
    trendEndHour=72,
)

strategy = LiveStrategy(data, emas, fractals, params)

engine = Engine(
    id='single',
    strategy=strategy)

engine.run()
engine.save(
    path = path,
    isFull = True)

engine.print_metrics()
engine.print_trades()
# engine.strategy.plot(
#     shouldShow = True
# )
engine.plot_trades(
    shouldShow = True
)
# engine.plot_equity()

