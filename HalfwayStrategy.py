from BaselineStrategy import BaselineStrategy
from model.Ticker import Ticker

class HalfwayStrategy(BaselineStrategy):

    def __init__(self):
        super().__init__()
        self.size = 1
        self.ticker = Ticker(
            symbol = 'MNQ',
            tick_value = 0.50,
            margin_requirement = 3552) # http://tradestation.com/pricing/futures-margin-requirements/

    def on_bar(self):

        self.bar_index += 1
        bar_index = self.bar_index

        is_flat = self.position_size == 0
        is_long = self.position_size > 0
        is_short = 0 > self.position_size

        if is_flat and bar_index % 321 == 0:
            self.buy(self.ticker, self.size)
            # print(f'{bar_index}: long enter')

        if is_long and bar_index % 987 == 0:
            self.flat(self.ticker, self.size)
            # print(f'{bar_index}: long exit')

        if is_flat and bar_index % 1113 == 0:
            self.sell(self.ticker, self.size)
            # print(f'{bar_index}: short enter')

        if is_short and bar_index % 3109 == 0:
            self.flat(self.ticker, self.size)
            # print(f'{bar_index}: short exit')
