from enum import Enum

class Fitness(Enum):
    
    PROFIT = 'profit'
    EXPECTANCY = 'expectancy'
    WIN_RATE = 'win_rate'
    AVERAGE_WIN = 'average_win'
    AVERAGE_LOSS = 'average_loss'
    DRAWDOWN = 'drawdown'
    DRAWDOWN_PER_PROFIT = 'drawdown_per_profit'

    @property
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

    @property
    def is_max(self):

        if self.name in [
            'profit',
            'expectancy',
            'win_rate',
            'average_win',
        ]: return True

        return False

    @property
    def color(self):

        # colors
        white = 'white'
        light_gray = '#262626'
        gray = '#1a1a1a'
        black = '#141414'
        blue = '#4287f5'
        aqua = '#42f5f5'
        green = '#42f578'
        red = '#f55a42'

        color = ''
        match self:
            case Fitness.PROFIT: color = blue
            case Fitness.EXPECTANCY: color = green
            case Fitness.WIN_RATE: color = aqua
            case Fitness.AVERAGE_WIN: color = red
            case Fitness.AVERAGE_LOSS: color = light_gray
            case Fitness.DRAWDOWN: color = gray
            case Fitness.DRAWDOWN_PER_PROFIT: color = white

        return color