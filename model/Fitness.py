from enum import Enum

class Fitness(Enum):
    
    PROFIT = 'profit'
    EXPECTANCY = 'expectancy'
    WIN_RATE = 'win_rate'
    AVERAGE_WIN = 'average_win'
    AVERAGE_LOSS = 'average_loss'
    DRAWDOWN = 'drawdown'
    DRAWDOWN_PER_PROFIT = 'drawdown_per_profit'
    
    def pretty(self):

        title = ''
        match self:
            case Fitness.PROFIT: title = 'Profit'
            case Fitness.EXPECTANCY: title = 'Expectancy'
            case Fitness.WIN_RATE: title = 'Win rate'
            case Fitness.AVERAGE_WIN: title = 'Average win'
            case Fitness.AVERAGE_LOSS: title = 'Average loss'
            case Fitness.DRAWDOWN: title = 'Drawdown'
            case Fitness.DRAWDOWN_PER_PROFIT: title = 'Drawdown per profit'

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
