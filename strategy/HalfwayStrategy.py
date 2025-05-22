from strategy.BaselineStrategy import BaselineStrategy
from model.Ticker import Ticker

class HalfwayStrategy(BaselineStrategy):

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
