from model.Order import Order

class BaselineStrategy():

    def __init__(self):
        self.current_idx = None
        self.bar_index = -1
        self.data = None
        self.orders = []

    def buy(self, ticker, size):
        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = 'long',
                size = size,
                idx = self.current_idx,
                bar_index = self.bar_index,
                price = self.close))

    def sell(self, ticker, size):
        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = 'short',
                size = -size,
                idx = self.current_idx,
                bar_index = self.bar_index,
                price = self.close))

    def flat(self, ticker, size):

        # flatten previous order
        last_order = self.orders[-1]
        if last_order.sentiment == 'long':
            size = -1
        if last_order.sentiment == 'short':
            size = 1

        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = 'flat',
                size = size,
                idx = self.current_idx,
                bar_index = self.bar_index,
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
