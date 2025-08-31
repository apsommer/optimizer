import time
import warnings

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import print_metrics
from utils.utils import *

''' single engine verify to tradingview'''
# INPUT ###########################################################

asset = 'ES'
num_months = 20
isNetwork = False
id = format_timestamp(datetime.now(), 'local')

params = LiveParams(
    fastMinutes = 25,
    disableEntryMinutes = 105,
    fastMomentumMinutes = 125,
    fastCrossoverPercent = 0,
    takeProfitPercent = 0.55,
    stopLossPercent = 0,
    fastAngleEntryFactor = 15,
    fastAngleExitFactor = 2050,
    slowMinutes = 2150,
    slowAngleFactor = 25,
    coolOffMinutes = 10,
    trendStartHour = 6,
    trendEndHour = 142
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

# init data and indicators
data = getOhlc(asset, num_months, isNetwork)
emas = unpack('emas', data_path)
fractals = unpack('fractals', data_path)

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