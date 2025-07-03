import numpy as np

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

        size = self.size # negative for shorts!
        point_value = self.entry_order.ticker.point_value

        entry_price = self.entry_order.price
        exit_price = self.exit_order.price

        return size * point_value * (exit_price - entry_price)

    def __repr__(self):

        # format to match tradingview
        exit = '\n\t' + str(self.id) + str(self.exit_order) + '\t' + str(round(self.profit)) + '\t' + self.exit_order.comment
        entry = '\n\t' + str(self.entry_order) + '\t\t' + self.entry_order.comment

        return exit + entry
