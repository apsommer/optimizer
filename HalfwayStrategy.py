from BaselineStrategy import BaselineStrategy
from sympy import *

class HalfwayStrategy(BaselineStrategy):

    def __init__(self):
        super().__init__()
        self.barIndex = -1

    def on_bar(self):

        ticker = 'NQ'
        size = 1

        self.barIndex += 1
        barIndex = self.barIndex

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        is_flat = self.position_size == 0
        is_long = self.position_size > 0
        is_short = 0 > self.position_size

        if is_flat and barIndex == 11:
            self.buy(ticker, size)

        if is_long and barIndex == 22:
            self.sell(ticker, size)

        if is_flat and barIndex == 33:
            self.sell(ticker, size)

        if is_short and barIndex == 44:
            self.buy(ticker, size)
