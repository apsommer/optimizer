class Order:
    def __init__(self, ticker, size, sentiment, idx, bar_index, price):
        self.ticker = ticker
        self.sentiment = sentiment # long, short, flat todo refactor to enum
        self.size = size
        self.idx = idx
        self.bar_index = bar_index
        self.price = price

    def __repr__(self):

        sentiment = self.sentiment
        if sentiment == 'flat': sentiment = ''

        return (
            sentiment + '\t' +
            self.idx.strftime('%b %d, %Y, %H:%M') + '\t' +
            str(round(self.price)))