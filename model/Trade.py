class Trade:
    def __init__(self, side, size, entry_order, exit_order):
        self.side = side # long, short
        self.size = size
        self.entry_order = entry_order
        self.exit_order = exit_order

    @property
    def is_open(self):
        return self.exit_order is None

    @property
    def profit(self):

        profit = 0
        if self.entry_order is None or self.exit_order is None:
            return profit

        entry_price = self.entry_order.price
        exit_price = self.exit_order.price
        tick_value = self.entry_order.ticker.tick_value

        if self.side == 'long':
            profit = tick_value * (exit_price - entry_price)
        if self.side == 'short':
            profit = tick_value * (entry_price - exit_price)
        return profit

    def __repr__(self):
        return f'\nside: {self.side}\nsize: {self.size}\nentry_order: {self.entry_order}\nexit_order: {self.exit_order}'
