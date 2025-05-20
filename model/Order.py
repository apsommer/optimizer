class Order:
    def __init__(self, ticker, size, sentiment, idx, bar_index, price):
        self.ticker = ticker
        self.sentiment = sentiment # long, short, flat
        self.size = size
        self.idx = idx
        self.bar_index = bar_index
        self.price = price

    def __repr__(self):
        return f'\n\tticker: {self.ticker}\n\tsentiment: {self.sentiment}\n\tsize: {self.size}\n\tidx: {self.idx}\n\tbar_index: {self.bar_index}\n\tprice: {self.price}'

