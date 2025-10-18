from model.Order import Order
from model.Ticker import Ticker


class BaselineStrategy():

    # Nasdaq 100, MNQ: 0.25, 0.50
    # S&P 500, MES (ES): 0.25, 1.25
    # Dow, MYM (YM): 1, 0.5
    # Nikkei, MNK (NKD): 5, 2.50

    # Euro/USD, 6E: 0.00005, 6.25
    # Ether, MET (ETH): 0.05, 0.05

    # Gold, MGC (GC): 0.1, 1
    # Silver, SIL (SI): 0.001, 1
    # Copper, MHG (HG): 0.0005, 1.25

    # Corn, MZC (ZC): 0.005, 2.50 ... p&l too large
    # Oil, MCL: 0.01, 1

    # 10-year, MTN (ZN): 0.015625, 1.5625

    @property
    def ticker(self):
        return Ticker(
            symbol = 'MCL',
            tick_size = 0.01,
            tick_value = 1,
            margin = 1 # todo remove
        )

    def __init__(self):
        self.current_idx = None
        self.bar_index = -1
        self.data = None
        self.orders = []
        self.params = None
        self.position = 0

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
        self.position += size

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
        self.position -= size

    @property
    def is_flat(self):
        return self.position == 0

    @property
    def is_long(self):
        return self.position > 0

    @property
    def is_short(self):
        return 0 > self.position

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
