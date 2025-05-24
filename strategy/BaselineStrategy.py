from model.Order import Order

class BaselineStrategy():

    def __init__(self):
        self.current_idx = None
        self.bar_index = -1
        self.data = None
        self.orders = []
        self.params = None

    def buy(self, ticker, size, sentiment):
        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = sentiment,
                size = size,
                idx = self.current_idx,
                bar_index = self.bar_index,
                price = self.close))

    def sell(self, ticker, size, sentiment):
        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = sentiment,
                size = -size,
                idx = self.current_idx,
                bar_index = self.bar_index,
                price = self.close))

    def flat(self, ticker, size, sentiment):
        if self.is_long:
            self.sell(ticker, size, sentiment)
        if self.is_short:
            self.buy(ticker, size, sentiment)

    @property
    def position_size(self):
        return sum([order.size for order in self.orders])

    @property
    def is_flat(self):
        return self.position_size == 0

    @property
    def is_long(self):
        return self.position_size > 0

    @property
    def is_short(self):
        return 0 > self.position_size

    @property
    def open(self):
        return self.data.loc[self.current_idx]['Open']

    @property
    def close(self):
        return self.data.loc[self.current_idx]['Close']

    """ Override by implementers """
    def on_bar(self):
        pass
