class Trade:
    def __init__(self, ticker, side, size, idx, type, price):
        self.ticker = ticker
        self.side = side
        self.size = size
        self.idx = idx
        self.type = type
        self.price = price

    # string representation of class, called "dunder" for double under underscores
    def __repr__(self):

        return f'\nticker: {self.ticker}\nside: {self.side}\nsize: {self.size}\nidx: {self.idx}\ntype: {self.type}\nprice: {self.price}\n'