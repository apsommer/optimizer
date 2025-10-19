import numpy as np

from utils.utils import format_timestamp

class Trade:
    def __init__(self, id, side, size, entry_order, exit_order):
        self.id = id
        self.side = side # long, short
        self.size = size
        self.entry_order = entry_order
        self.exit_order = exit_order

    @property
    def is_open(self):
        return self.exit_order is None

    @property
    def is_closed(self):
        return self.exit_order is not None

    @property
    def is_long(self):
        return self.side == 'long'

    @property
    def is_short(self):
        return self.side == 'short'

    @property
    def profit(self):

        if self.entry_order is None or self.exit_order is None:
            return np.nan

        size = self.size
        side = self.side # equal to entry order sentiment

        tick_size = self.entry_order.ticker.tick_size
        tick_value = self.entry_order.ticker.tick_value

        entry_price = self.entry_order.price
        exit_price = self.exit_order.price

        delta_price = exit_price - entry_price
        if side == 'short': delta_price = entry_price - exit_price

        return size * tick_value * delta_price / tick_size

    def __repr__(self):

        # INPUT ########
        decimals = 2
        ################

        # format to match tradingview
        exit = ('\n\t' + str(self.id) + '\t' + format_timestamp(self.exit_order.idx) + '\t' +
                str(round(self.exit_order.price, decimals)) + '\t' + str(round(self.profit, decimals)) + '\t' + self.exit_order.comment)

        entry = ('\n\t' + str(self.entry_order.sentiment) + '\t' + format_timestamp(self.entry_order.idx) + '\t' +
                 str(round(self.entry_order.price, decimals)))

        return exit + entry
