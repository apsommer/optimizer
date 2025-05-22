from strategy.BaselineStrategy import BaselineStrategy
from model.Ticker import Ticker

class HalfwayStrategy(BaselineStrategy):

    def __init__(self):
        super().__init__()

        self.is_strategy_enabled = False
        self.strategy_start_index = -1
        self.raw_fast = 0.0
        self.raw_slow = 0.0
        self.fast = 0.0
        self.slow = 0.0
        self.fast_slope = 0.0
        self.slow_slope = 0.0


    @property
    def ticker(self):
        return Ticker(
            symbol = 'MNQ',
            tick_value = 0.50,
            margin = 0.10) # 10% of underlying, http://tradestation.com/pricing/futures-margin-requirements/

    @property
    def size(self):
        return 1

    def on_bar(self):

        self.bar_index += 1

        fast_minutes = 25
        disable_entry_minutes = 105
        fast_momentum_minutes = 135
        fast_crossover_percent = 0
        take_profit_percent = 0.35
        fast_angle_factor = 15
        slow_minutes = 2355
        slow_angle_factor = 20
        entry_restriction_minutes = 0
        entry_restriction_percent = 0

        cool_off_minutes = 5
        position_entry_minutes = 1

        # entry long
        if self.is_flat and self.bar_index % 321 == 0:
            self.buy(self.ticker, self.size, 'long')

        # exit long
        elif self.is_long and self.bar_index % 987 == 0:
            self.flat(self.ticker, self.size, 'flat')

        # entry short
        elif self.is_flat and self.bar_index % 1113 == 0:
            self.sell(self.ticker, self.size, 'short')

        # exit short
        elif self.is_short and self.bar_index % 3109 == 0:
            self.flat(self.ticker, self.size, 'flat')
