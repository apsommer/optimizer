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

        # entry
        side = self.side
        point_value = self.entry_order.ticker.point_value
        entry_price = self.entry_order.price
        exit_price = self.exit_order.price

        profit = point_value * (exit_price - entry_price) # long
        if side == 'short': profit = point_value * (entry_price - exit_price) # short

        return profit

    def print_tv(self):

        print(f'\ntrade: {self.id}')

        if self.exit_order is None: line = 'open'
        else: line = self.exit_order.format_tv() + '\t' + str(self.profit)
        print(line)

        print(self.entry_order.format_tv())

    def __repr__(self):
        return f'\nid: {self.id}\nside: {self.side}\nsize: {self.size}\nentry_order: {self.entry_order}\nexit_order: {self.exit_order}'
