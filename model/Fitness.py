from enum import Enum

class Fitness(Enum):
    MAX_PROFIT = 'max_profit'
    MAX_EXPECTANCY = 'max_expectancy'
    MAX_WIN_RATE = 'max_win_rate'
    MAX_AVERAGE_WIN = 'max_average_win'
    MIN_AVERAGE_LOSS = 'min_average_loss'
    MIN_DRAWDOWN = 'min_drawdown'
    MIN_DRAWDOWN_PER_PROFIT = 'min_drawdown_per_profit'