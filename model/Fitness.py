import random
from enum import Enum
from model.Metric import Metric
from utils.constants import *

class Fitness(Enum):

    # key is name of engine metric
    PROFIT = 'profit'
    PROFIT_FACTOR = 'profit_factor'
    EXPECTANCY = 'expectancy'
    WIN_RATE = 'win_rate'
    AVERAGE_WIN = 'average_win'
    AVERAGE_LOSS = 'average_loss'
    DRAWDOWN = 'drawdown'
    DRAWDOWN_PER_PROFIT = 'drawdown_per_profit'
    CORRELATION = 'correlation'
    NUM_TRADES = 'num_trades'

    @property
    def pretty(self):
        match self:
            case Fitness.PROFIT: return 'Profit'
            case Fitness.PROFIT_FACTOR: return 'Profit Factor'
            case Fitness.EXPECTANCY: return 'Expectancy'
            case Fitness.WIN_RATE: return 'Win rate'
            case Fitness.AVERAGE_WIN: return 'Average win'
            case Fitness.AVERAGE_LOSS: return 'Average loss'
            case Fitness.DRAWDOWN: return 'Drawdown'
            case Fitness.DRAWDOWN_PER_PROFIT: return 'Drawdown per profit'
            case Fitness.CORRELATION: return 'Linear correlation'
            case Fitness.NUM_TRADES: return 'Number of trades'

    @property
    def color(self):
        i = random.randint(0, len(colors) - 1)
        return colors[i]