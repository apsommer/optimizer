class Order:
    def __init__(self, ticker, size, side, idx, price):
        self.ticker = ticker
        self.side = side # long, short, flat
        self.size = size
        self.idx = idx
        self.price = price

    # string representation of class, called "dunder" for double under underscores
    def __repr__(self):
        return f'\nticker: {self.ticker}\nside: {self.side}\nsize: {self.size}\nidx: {self.idx}\nprice: {self.price}\n'

