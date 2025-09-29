from model.Order import Order
from model.Ticker import Ticker


class BaselineStrategy():

    # Ether, MET (ETH): 0.05, 0.05
    # Gold, MGC (GC): 0.1, 1
    # Oil, MCL (QM): 0.01, 1
    # Dow, MYM (YM): 1, 0.5
    # Silver, SIL (SI): 0.001, 1
    # 10-year, MTN (ZN): 0.015625, 1.5625
    # Nikkei, MNK (NKD): 5, 2.50
    # Corn, MZC (ZC): 0.005, 2.50
    @property
    def ticker(self):
        return Ticker(
            symbol = 'ZC',
            tick_size = 0.005,
            tick_value = 2.50,
            margin = 1 # todo remove
        )

    def __init__(self):
        self.current_idx = None
        self.bar_index = -1
        self.data = None
        self.orders = []
        self.params = None

    def buy(self, ticker, size, comment = ''):
        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = 'long',
                size = size,
                idx = self.current_idx,
                bar_index = self.bar_index,
                price = self.close,
                comment = comment))

    def sell(self, ticker, size, comment = ''):
        self.orders.append(
            Order(
                ticker = ticker,
                sentiment = 'short',
                size = -size,
                idx = self.current_idx,
                bar_index = self.bar_index,
                price = self.close,
                comment = comment))

    @property
    def position_size(self):
        return sum([order.size for order in self.orders]) # todo fix perf

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

    @property
    def is_last_bar(self):
        return self.current_idx == self.data.index[-1]

    """ Override by implementers """
    def on_bar(self):
        pass
