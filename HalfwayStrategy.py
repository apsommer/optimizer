from BaselineStrategy import BaselineStrategy
from sympy import *

class HalfwayStrategy(BaselineStrategy):

    def __init__(self):
        super().__init__()

    def on_bar(self):

        ticker = 'NQ'
        size = 1

        self.bar_index += 1
        bar_index = self.bar_index

        is_flat = self.position_size == 0
        is_long = self.position_size > 0
        is_short = 0 > self.position_size

        if is_flat and bar_index == 3000:
            self.buy(ticker, size)
            # print(f'{bar_index}: long enter')

        if is_long and bar_index == 8000:
            self.flat(ticker, size)
            # print(f'{bar_index}: long exit')

        if is_flat and bar_index == 20000:
            self.sell(ticker, size)
            # print(f'{bar_index}: short enter')

        if is_short and bar_index == 30000:
            self.flat(ticker, size)
            # print(f'{bar_index}: short exit')
