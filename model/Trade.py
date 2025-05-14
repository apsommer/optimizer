class Trade:
    def __init__(self, ticker, side, size, entry_order, exit_order):
        self.ticker = ticker
        self.side = side # long, short
        self.size = size
        self.entry_order = entry_order
        self.exit_order = exit_order

    def is_new(self):
        return self.entry_order is None and self.exit_order is None

    def is_open(self):
        return self.entry_order is not None and self.exit_order is None

    def is_closed(self):
        return self.entry_order is not None and self.exit_order is not None

    # string representation of class, called "dunder" for double under underscores
    def __repr__(self):
        return f'\nticker: {self.ticker}\nside: {self.side}\nsize: {self.size}\nidx: {self.idx}\nentry_order: {self.entry_order}\nexit_order: {self.exit_order}\n'
