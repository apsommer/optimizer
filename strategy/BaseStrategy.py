from model.Order import Order

class BaselineStrategy():

    def __init__(self):
        self.current_idx = None
        self.bar_index = -1
        self.orders = []
        self.params = None

    def buy(self, ticker, size, price, sentiment='long'):
        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = sentiment,
                size = size,
                idx = self.current_idx,
                bar_index = self.bar_index,
                price = price))

    def sell(self, ticker, size, price, sentiment='short'):
        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = sentiment,
                size = -size,
                idx = self.current_idx,
                bar_index = self.bar_index,
                price = price))

    def flat(self, ticker, size, price, sentiment='flat'):
        if self.is_long:
            self.sell(ticker, size, price, sentiment)
        if self.is_short:
            self.buy(ticker, size, price, sentiment)

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

    """ Override by implementers """
    def on_bar(self):
        pass
