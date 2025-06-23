from analysis.Engine import Engine
from strategy.FastParams import FastParams
from strategy.FastStrategy import FastStrategy
from utils.utils import getOhlc, unpack

def init_engine(num_months, isNetwork, path):

    data = getOhlc(num_months, isNetwork)

    # build_indicators(data, path)
    emas = unpack('emas', path)
    slopes = unpack('slopes', path)
    fractals = unpack('fractals', path)

    params = FastParams(
        takeProfitPercent=1,
        stopLossPercent=1,
        proximityPercent=2)

    strategy = FastStrategy(
        data=data,
        emas=emas,
        slopes=slopes,
        fractals=fractals,
        params=params)

    engine = Engine(
        id='single',
        strategy=strategy)

    return engine