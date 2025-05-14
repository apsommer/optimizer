from model.Order import Order

class BaselineStrategy():

    def __init__(self):
        self.current_idx = None
        self.data = None
        self.orders = []

    def buy(self, ticker = 'NQ', size = 1):
        self.orders.append(
            Order(
                ticker = ticker,
                side = 'buy',
                size = size,
                idx = self.current_idx, # todo where is this updated?
                price = self.close))

    def sell(self, ticker = 'NQ', size = 1):
        self.orders.append(
            Order(
                ticker = ticker,
                side = 'sell',
                size = -size,
                idx = self.current_idx,
                price = self.close))

    @property
    def position_size(self):
        return sum([order.size for order in self.orders])

    @property
    def open(self):
        return self.data.loc[self.current_idx]['Open']

    @property
    def close(self):
        return self.data.loc[self.current_idx]['Close']

    """ Override by implementers """
    def on_bar(self):
        pass
