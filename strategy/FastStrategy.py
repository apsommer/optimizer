import numpy as np
import pandas as pd
from strategy.BaseStrategy import BaselineStrategy
from model.Ticker import Ticker
from utils.constants import *
from utils.utils import *
import finplot as fplt
import matplotlib as mpl

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

        self.num = params.num

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
        num = self.num

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
            and p >= num
        )
        if isEntryLong:
            self.buy(ticker, size)

        # entry short
        isEntryShort = (
            is_flat
            and 10 - num >= p
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
        isExitLongMomentum = is_long and 10 - num >= p
        isExitShortMomentum = is_short and p >= num

        # exit on last bar of data
        isExitLastBar = False
        if idx == self.data.index[-1]:
            if is_long or is_short:
                isExitLastBar = True

        # exit long
        isExitLong = (
            isExitLongTakeProfit
            or isExitLongMomentum
            or isExitLastBar
        )
        if isExitLong:
            self.flat(ticker, size)

        # exit short
        isExitShort = (
            isExitShortTakeProfit
            or isExitShortMomentum
            or isExitLastBar
        )
        if isExitShort:
            self.flat(ticker, size)

    def plot(self):

        ax = init_plot(0, 'Strategy')

        # candlestick ohlc
        data = self.data
        fplt.candlestick_ochl(data[['Open', 'Close', 'High', 'Low']], ax=ax, draw_body=False)

        # color ribbon
        crest = sns.color_palette("crest", as_cmap=True)
        colors = crest(np.linspace(0, 1, len(self.avgs.columns)))

        # plot ribbon
        for i, column in enumerate(self.avgs.columns):
            if 'avg' in column:
                color = mpl.colors.rgb2hex(colors[i])
                fplt.plot(self.avgs.loc[:, column], color=color, width=2, ax=ax)

        fplt.show()