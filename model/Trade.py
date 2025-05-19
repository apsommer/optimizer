class Trade:
    def __init__(self, ticker, side, size, entry_order, exit_order):
        self.ticker = ticker
        self.side = side # long, short
        self.size = size
        self.entry_order = entry_order
        self.exit_order = exit_order

    @property
    def profit(self):

        entry_price = self.entry_order.price
        exit_price = self.exit_order.price

        if entry_price is None or exit_price is None:
            return None
        if self.side == 'long':
            return tick_value * (exit_price - entry_price)
        if self.side == 'short':
            return tick_value * (entry_price - exit_price)

    # string representation of class, called "dunder" for double under underscores
    def __repr__(self):
        return f'\nticker: {self.ticker}\nside: {self.side}\nsize: {self.size}\nentry_order: {self.entry_order}\nexit_order: {self.exit_order}\n'
