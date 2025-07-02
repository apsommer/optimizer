from utils.metrics import format_timestamp


class Order:
    def __init__(self, ticker, size, sentiment, idx, bar_index, price, comment):
        self.ticker = ticker
        self.sentiment = sentiment # long, short, flat todo refactor to enum
        self.size = size
        self.idx = idx
        self.bar_index = bar_index
        self.price = price
        self.comment = comment

    def __repr__(self):

        sentiment = self.sentiment
        if sentiment == 'flat': sentiment = ''

        return (
            sentiment + '\t' +
            format_timestamp(self.idx) + '\t\t' +
            str(round(self.price)))