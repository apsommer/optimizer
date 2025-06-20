import warnings

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import print_metrics
from utils.plots import plot_equity, plot_trades
from utils.utils import *

os.system('clear')
warnings.filterwarnings('ignore')

path = 'wfa/NQ_3mon/20_14'
indicators = unpack('indicators', path)
data = getOhlc(3, False)

params = LiveParams(
    fastMinutes=25,
    disableEntryMinutes=105,
    fastMomentumMinutes=135,
    fastCrossoverPercent=80,
    takeProfitPercent=0.5,
    fastAngleFactor=15,
    slowMinutes=2555,
    slowAngleFactor=20,
    coolOffMinutes=5)

strategy = LiveStrategy(data, indicators, params)
engine = Engine(
    id = 'scratch',
    strategy = strategy)
engine.run()

print_metrics(engine.metrics)
plot_trades(engine)
