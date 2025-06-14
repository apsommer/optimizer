from enum import Enum

class Fitness(Enum):
    MAX_PROFIT = 'profit'
    MAX_EXPECTANCY = 'expectancy'
    MAX_WIN_RATE = 'win_rate'
    MAX_AVERAGE_WIN = 'average_win'
    MIN_AVERAGE_LOSS = 'average_loss'
    MIN_DRAWDOWN = 'drawdown'
    MIN_DRAWDOWN_PER_PROFIT = 'drawdown_per_profit'

    def pretty(self):

        title = ''
        match self:
            case Fitness.MAX_PROFIT: title = 'Profit'
            case Fitness.MAX_EXPECTANCY: title = 'Expectancy'
            case Fitness.MAX_WIN_RATE: title = 'Win rate'
            case Fitness.MAX_AVERAGE_WIN: title = 'Average win'
            case Fitness.MIN_AVERAGE_LOSS: title = 'Average loss'
            case Fitness.MIN_DRAWDOWN: title = 'Drawdown'
            case Fitness.MIN_DRAWDOWN_PER_PROFIT: title = 'Drawdown per profit'

        return title

    def is_max(self):

        max = [
            'profit',
            'expectancy',
            'win_rate',
            'average_win',
        ]

        if self.name not in max: return False
        return True

    def is_min(self):

        min = [
            'average_loss',
            'drawdown',
            'drawdown_per_profit',
        ]

        if self.name not in min: return False
        return True