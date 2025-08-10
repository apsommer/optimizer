import time
import warnings

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import print_metrics
from utils.utils import *

''' single engine verify to tradingview'''
# INPUT ###########################################################

asset = 'NQ'
num_months = 15
isNetwork = False
id = format_timestamp(datetime.now(), 'local')

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
params = LiveParams(
    fastMinutes = 20,
    disableEntryMinutes = 110,
    fastMomentumMinutes = 95,
    fastCrossoverPercent = 0,
    takeProfitPercent = 0.75,
    stopLossPercent = 0,
    fastAngleEntryFactor = 0,
    fastAngleExitFactor = 2055,
    slowMinutes = 2555,
    slowAngleFactor = 15,
    coolOffMinutes = 5,
    trendStartHour = 4,
    trendEndHour = 72
)
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