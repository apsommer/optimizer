class Trade:
    def __init__(self, ticker, side, size, idx, entry_order, exit_order):
        self.ticker = ticker
        self.side = side # long, short
        self.size = size
        self.idx = idx
        self.entry_order = entry_order
        self.exit_order = exit_order

    # string representation of class, called "dunder" for double under underscores
    def __repr__(self):
        return f'\nticker: {self.ticker}\nside: {self.side}\nsize: {self.size}\nidx: {self.idx}\nentry_order: {self.entry_order}\nexit_order: {self.exit_order}\n'
