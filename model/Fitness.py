import random
from enum import Enum
import seaborn as sns

from utils.constants import *


class Fitness(Enum):
    
    PROFIT = 'profit'
    # PROFIT_FACTOR = 'profit_factor'
    # EXPECTANCY = 'expectancy'
    # WIN_RATE = 'win_rate'
    # AVERAGE_WIN = 'average_win'
    # AVERAGE_LOSS = 'average_loss'
    # DRAWDOWN = 'drawdown'
    # DRAWDOWN_PER_PROFIT = 'drawdown_per_profit'

    @property
    def pretty(self):
        title = ''
        match self:
            case Fitness.PROFIT: title = 'Profit'
            case Fitness.PROFIT_FACTOR: title = 'Profit Factor'
            case Fitness.EXPECTANCY: title = 'Expectancy'
            case Fitness.WIN_RATE: title = 'Win rate'
            case Fitness.AVERAGE_WIN: title = 'Average win'
            case Fitness.AVERAGE_LOSS: title = 'Average loss'
            case Fitness.DRAWDOWN: title = 'Drawdown'
            case Fitness.DRAWDOWN_PER_PROFIT: title = 'Drawdown per profit'

        return title

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