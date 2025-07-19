from enum import Enum
from utils.constants import *

class Fitness(Enum):

    PROFIT = 'profit'
    PROFIT_FACTOR = 'profit_factor'
    EXPECTANCY = 'expectancy'
    WIN_RATE = 'win_rate'
    AVERAGE_WIN = 'average_win'
    AVERAGE_LOSS = 'average_loss'
    DRAWDOWN = 'drawdown'
    DRAWDOWN_PER_PROFIT = 'drawdown_per_profit'
    CORRELATION = 'correlation'

    @property
    def unit(self):
        match self:
            case Fitness.PROFIT: return 'USD'
            case Fitness.PROFIT_FACTOR: return None
            case Fitness.EXPECTANCY: return 'USD'
            case Fitness.WIN_RATE: return '%'
            case Fitness.AVERAGE_WIN: return 'USD'
            case Fitness.AVERAGE_LOSS: return 'USD'
            case Fitness.DRAWDOWN: return 'USD'
            case Fitness.DRAWDOWN_PER_PROFIT: return 'USD'
            case Fitness.CORRELATION: return None

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

    @property
    def color(self):
        match self:
            case Fitness.PROFIT: return blue
            case Fitness.PROFIT_FACTOR: return yellow
            case Fitness.EXPECTANCY: return orange
            case Fitness.WIN_RATE: return green
            case Fitness.AVERAGE_WIN: return red
            case Fitness.AVERAGE_LOSS: return purple
            case Fitness.DRAWDOWN: return brown
            case Fitness.DRAWDOWN_PER_PROFIT: return pink
            case Fitness.CORRELATION: return gray