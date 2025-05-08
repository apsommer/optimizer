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
        return f'Trade: {self.idx} {self.ticker} {self.size} @ {self.price}'