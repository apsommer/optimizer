import time
import warnings
from copy import deepcopy

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import print_metrics
from utils.utils import *

''' single engine verify to tradingview'''
# INPUT ###########################################################

asset = 'GC'
num_months = 5
isNetwork = True

params = LiveParams(
    fastMinutes = 65,
    disableEntryMinutes = 135,
    fastMomentumMinutes = 120,
    fastCrossoverPercent = 0,
    takeProfitPercent = 2.3,
    stopLossPercent = 0,
    fastAngleEntryFactor = 30,
    fastAngleExitFactor = 2975,
    slowMinutes = 2755,
    slowAngleFactor = 15,
    coolOffMinutes = 15,
    trendStartHour = 8,
    trendEndHour = 0
)

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
np.set_printoptions(threshold = 3)
start_time = time.time()

# organize outputs
data_name = asset + '_' + str(num_months) + 'm'
data_path = 'data/' + data_name
parent_path = 'single/' + data_name
id = format_timestamp(datetime.now(), 'local')

# init data
data = getOhlc(asset, num_months, isNetwork)

# get indicators
# emas = unpack('emas', data_path)
# fractals = unpack('fractals', data_path)

# init indicators
opt = deepcopy(params)
opt.fastMinutes = [params.fastMinutes]
opt.slowMinutes = [params.slowMinutes]
emas, fractals = getIndicators(data, opt, data_path)

# define strategy
strategy = LiveStrategy(data, emas, fractals, params)
engine = Engine(id, strategy)
engine.run(disable = False)
engine.save(parent_path, False)

# display results
engine.print_metrics()
engine.print_trades()
engine.plot_trades()
engine.plot_equity(shouldShow = False)

fplt.show()