import numpy as np
import pandas as pd
from strategy.BaseStrategy import BaselineStrategy
from model.Ticker import Ticker
from utils.constants import *
from utils.utils import *
import finplot as fplt

class FastStrategy(BaselineStrategy):

    @property
    def ticker(self):
        return Ticker(
            symbol = 'MNQ',
            tick_size = 0.25,
            point_value = 2, # NQ = 20, MNQ = 2
            margin = 0.5) # 10% of underlying, http://tradestation.com/pricing/futures-margin-requirements/

    @property
    def size(self):
        return 1

    def __init__(self, data, avgs, params):
        super().__init__()

        self.data = data
        self.params = params
        self.avgs = avgs

        takeProfitPercent = params.takeProfitPercent
        self.takeProfit = takeProfitPercent / 100.0
        self.longTakeProfit = np.nan
        self.shortTakeProfit = np.nan

    def on_bar(self):

        data = self.data
        params = self.params
        avgs = self.avgs

        # index
        idx = self.current_idx
        self.bar_index += 1
        bar_index = self.bar_index

        # data
        open = self.data.Open[idx]
        high = self.data.High[idx]
        low = self.data.Low[idx]
        close = self.data.Close[idx]

        # position
        is_flat = self.is_flat
        is_long = self.is_long
        is_short = self.is_short

        ticker = self.ticker
        size = self.size

        # strategy
        takeProfit = self.takeProfit
        longTakeProfit = self.longTakeProfit
        shortTakeProfit = self.shortTakeProfit

        ################################################################################################################

        # count how many averages are positive/negative
        p = 0
        for column in avgs.columns:
            if 'slope' in column:
                value = avgs.loc[idx, column]
                if value > 0: p += 1

        # entry long
        isEntryLong = (
            is_flat
            and p > 9
        )
        if isEntryLong:
            self.buy(ticker, size)

        # entry short
        isEntryShort = (
            is_flat
            and 1 > p
        )
        if isEntryShort:
            self.sell(ticker, size)

        ################################################################################################################

        # exit, long take profit
        if isEntryLong: longTakeProfit = (1 + takeProfit) * close
        elif not is_long: longTakeProfit = np.nan
        self.longTakeProfit = longTakeProfit
        isExitLongTakeProfit = high > longTakeProfit

        # exit, short take profit:
        if isEntryShort: shortTakeProfit = (1 - takeProfit) * close
        elif not is_short: shortTakeProfit = np.nan
        self.shortTakeProfit = shortTakeProfit
        isExitShortTakeProfit = shortTakeProfit > low

        # exit, momentum
        isExitLongMomentum = is_long and 1 > p
        isExitShortMomentum = is_short and p > 9

        # exit long
        isExitLong = (
            isExitLongTakeProfit
            or isExitLongMomentum
        )
        if isExitLong:
            self.flat(ticker, size)

        # exit short
        isExitShort = (
            isExitShortTakeProfit
            or isExitShortMomentum
        )
        if isExitShort:
            self.flat(ticker, size)

    def plot(self):

        ax = init_plot(0, 'Strategy')

        # candlestick ohlc
        data = self.data
        fplt.candlestick_ochl(data[['Open', 'Close', 'High', 'Low']], ax=ax)

        for column in self.avgs.columns:
            if 'avg' in column:
                fplt.plot(self.avgs.loc[:, column], color=blue, width=2, ax=ax)

        fplt.show()