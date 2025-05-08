class Order:
    def __init__(self, ticker, size, side, idx, type ='market', limit_price = None):
        self.ticker = ticker
        self.side = side
        self.size = size
        self.idx = idx
        self.type = type
        self.limit_price = limit_price