class Order:
    def __init__(self, ticker, size, sentiment, idx, price):
        self.ticker = ticker
        self.sentiment = sentiment # long, short, flat
        self.size = size
        self.idx = idx
        self.price = price

    # string representation of class, called "dunder" for double under underscores
    def __repr__(self):
        return f'\nticker: {self.ticker}\nside: {self.sentiment}\nsize: {self.size}\nidx: {self.idx}\nprice: {self.price}\n'

