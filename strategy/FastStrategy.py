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

    def __init__(self, data, emas, slopes, params):
        super().__init__()

        self.data = data
        self.params = params
        self.emas = emas
        self.slopes = slopes

        takeProfitPercent = params.takeProfitPercent
        self.takeProfit = takeProfitPercent / 100.0
        self.longTakeProfit = np.nan
        self.shortTakeProfit = np.nan

        stopLossPercent = params.stopLossPercent
        self.stopLoss = stopLossPercent / 100.0
        self.longStopLoss = np.nan
        self.shortStopLoss = np.nan

        self.num = params.num

    def on_bar(self):

        data = self.data
        params = self.params
        emas = self.emas
        slopes = self.slopes

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
        stopLoss = self.stopLoss
        longStopLoss = self.longStopLoss
        shortStopLoss = self.shortStopLoss

        ################################################################################################################

        positives = 0
        slowestEma = 0

        # get slowest ema
        for min in emas.columns:
            ema = emas.loc[idx, min]
            if min == 2160:
                slowestEma = ema

        # count bullish slopes
        positives = 0
        for min in slopes.columns:
            slope = slopes.loc[idx, min]
            if slope > 0: positives += 1

        # entry long
        isEntryLong = (
            is_flat
            and positives == 10
            and low < slowestEma < close
        )
        if isEntryLong:
            self.buy(ticker, size)

        # entry short
        isEntryShort = (
            is_flat
            and positives == 0
            and high > slowestEma > close
        )
        if isEntryShort:
            self.sell(ticker, size)

        ################################################################################################################

        # exit, long take profit
        if isEntryLong: longTakeProfit = (1 + takeProfit) * close
        elif not is_long: longTakeProfit = np.nan
        self.longTakeProfit = longTakeProfit
        isExitLongTakeProfit = high > longTakeProfit

        # exit, short take profit
        if isEntryShort: shortTakeProfit = (1 - takeProfit) * close
        elif not is_short: shortTakeProfit = np.nan
        self.shortTakeProfit = shortTakeProfit
        isExitShortTakeProfit = shortTakeProfit > low

        # exit, long stop loss
        if isEntryLong: longStopLoss = (1 - stopLoss) * close
        elif not is_long: longStopLoss = np.nan
        self.longStopLoss = longStopLoss
        isExitLongStopLoss = longStopLoss > low

        # exit, short stop loss
        if isEntryShort: shortStopLoss = (1 + stopLoss) * close
        elif not is_short: shortStopLoss = np.nan
        self.shortStopLoss = shortStopLoss
        isExitShortStopLoss = high > shortStopLoss

        # exit on last bar of data
        isExitLastBar = False
        if idx == self.data.index[-1]:
            if is_long or is_short:
                isExitLastBar = True

        # exit long
        isExitLong = (
            isExitLongTakeProfit
            or isExitLongStopLoss
            or isExitLastBar
        )
        if isExitLong:
            self.flat(ticker, size)

        # exit short
        isExitShort = (
            isExitShortTakeProfit
            or isExitShortStopLoss
            or isExitLastBar
        )
        if isExitShort:
            self.flat(ticker, size)

    def plot(self):

        ax = init_plot(1, 'Strategy')

        # candlestick ohlc
        data = self.data
        fplt.candlestick_ochl(data[['Open', 'Close', 'High', 'Low']], ax=ax, draw_body=False)

        # color ribbon
        crest = sns.color_palette("crest", as_cmap=True)
        colors = crest(np.linspace(0, 1, 10))

        # plot ribbon
        emas = self.emas
        for i, min in enumerate(emas.columns):
            color = mpl.colors.rgb2hex(colors[i])
            fplt.plot(emas.loc[:, min], color=color, width=2, ax=ax)

        fplt.show()