from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.utils import getOhlc, unpack

def init_engine(num_months, isNetwork, path):

    data = getOhlc(num_months, isNetwork)

    # build_indicators(data, path)
    emas = unpack('emas', path)
    fractals = unpack('fractals', path)

    params = LiveParams(
        fastMinutes = 25,
        disableEntryMinutes = 105,
        fastMomentumMinutes = 95, # [65, 75, 85, 95, 105, 115, 125],
        fastCrossoverPercent = 0,
        takeProfitPercent = .4, # [.3, .35, .4, .45, .5],
        fastAngleFactor = 0,
        slowMinutes = 5555, # [2555, 5555],
        slowAngleFactor = 0,
        coolOffMinutes = 5,
        trendStartHour = 4,
        trendEndHour = 48,
    )

    strategy = LiveStrategy(data, emas, fractals, params)

    engine = Engine(
        id='single',
        strategy=strategy)

    return engine