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

    def __init__(self, data, emas, slopes, fractals, params):
        super().__init__()

        self.data = data
        self.params = params
        self.emas = emas
        self.slopes = slopes
        self.fractals = fractals

        # unpack params
        takeProfitPercent = params.takeProfitPercent
        stopLossRatio = params.stopLossRatio
        slowAngleFactor = params.slowAngleFactor

        self.takeProfit = takeProfitPercent / 100.0
        self.longTakeProfit = np.nan
        self.shortTakeProfit = np.nan

        # self.stopLoss = stopLossRatio * self.takeProfit
        self.longStopLoss = np.nan
        self.shortStopLoss = np.nan

        self.slowAngle = slowAngleFactor / 1000.0

        self.longEntryBarIndex = -1
        self.shortEntryBarIndex = -1

    def on_bar(self):

        # index
        idx = self.current_idx
        self.bar_index += 1
        bar_index = self.bar_index

        data = self.data
        params = self.params
        emas = self.emas
        slopes = self.slopes
        fractals = self.fractals

        # data
        open = data.Open[idx]
        high = data.High[idx]
        low = data.Low[idx]
        close = data.Close[idx]

        # fastest and slowest average todo refactor to df
        fastEma = emas.loc[idx, 550]
        fastestEma = emas.loc[idx, 50]
        fastestSlope = slopes.loc[idx, 50]
        slowestEma = emas.loc[idx, 5050]
        slowestSlope = slopes.loc[idx, 5050]

        # fractal points
        buyFractal = fractals.loc[idx, 'buyFractal']
        sellFractal = fractals.loc[idx, 'sellFractal']

        # position
        is_flat = self.is_flat
        is_long = self.is_long
        is_short = self.is_short

        # strategy
        takeProfit = self.takeProfit
        longTakeProfit = self.longTakeProfit
        shortTakeProfit = self.shortTakeProfit
        # stopLoss = self.stopLoss
        # longStopLoss = self.longStopLoss
        # shortStopLoss = self.shortStopLoss
        isExitLastBar = False
        slowAngle = self.slowAngle

        # orders
        ticker = self.ticker
        size = self.size

        ################################################################################################################

        # entry long todo become a billionaire
        isEntryLong = (
            is_flat
            and slowestSlope > slowAngle
            and fastEma > fastestEma
            and sellFractal == low # next sell fractal
        )
        if isEntryLong:
            self.longEntryBarIndex = bar_index
            self.buy(ticker, size)

        # entry short
        isEntryShort = (
            is_flat
            and -slowAngle > slowestSlope
            and fastestEma > fastEma
            and fastestEma > close
            and buyFractal == high # next buy fractal
        )
        if isEntryShort:
            self.shortEntryBarIndex = bar_index
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

        # # exit, long stop loss
        # if isEntryLong: longStopLoss = close - 0.5 * (close - slowestEma)
        # elif not is_long: longStopLoss = np.nan
        # # self.longStopLoss = longStopLoss
        # self.longStopLoss = close - 0.5 * (close - slowestEma)
        # isExitLongStopLoss = longStopLoss > low
        #
        # # exit, short stop loss
        # if isEntryShort:
        #     shortStopLoss = close + 0.5 * (slowestEma - close)
        # elif not is_short: shortStopLoss = np.nan
        # # self.shortStopLoss = shortStopLoss
        # self.shortStopLoss = close + 0.5 * (slowestEma - close)
        # isExitShortStopLoss = high > shortStopLoss

        # exit, crossover regime change
        isExitLongCrossover = is_long and slowestEma > low
        isExitShortCrossover = is_short and high > slowestEma

        # # exit, timeout
        # isExitLongTimeout = is_long and bar_index - self.longEntryBarIndex > 5
        # isExitShortTimeout = is_short and bar_index - self.shortEntryBarIndex > 5

        # exit long
        isExitLong = (
            isExitLongTakeProfit
            # or isExitLongStopLoss
            or isExitLongCrossover
            # or isExitLongTimeout
            or self.is_last_bar)
        if isExitLong:
            self.flat(ticker, size)

        # exit short
        isExitShort = (
            isExitShortTakeProfit
            # or isExitShortStopLoss
            or isExitShortCrossover
            # or isExitShortTimeout
            or self.is_last_bar)
        if isExitShort:
            self.flat(ticker, size)

    def plot(self, title = 'Strategy'):

        ax = init_plot(0, title)

        # candlestick ohlc
        data = self.data
        fplt.candlestick_ochl(data[['Open', 'Close', 'High', 'Low']], ax=ax, draw_body=False)

        # color ribbon
        crest = sns.color_palette("crest", as_cmap=True)
        colors = crest(np.linspace(0, 1, 10))

        # plot ribbon
        emas = self.emas
        for i, min in enumerate(emas.columns):
            color = mpl.colors.rgb2hex(colors[i % 10])
            fplt.plot(emas.loc[:, min], color=color, width=2, ax=ax)

        buyFractals = self.fractals.loc[:, 'buyFractal']
        sellFractals = self.fractals.loc[:, 'sellFractal']

        # init dataframe plot entities
        entities = pd.DataFrame(
            index = data.index,
            dtype = float,
            columns = [
                'buyFractal',
                'sellFractal'])

        lastBuyPrice, lastSellPrice = 0, 0
        for idx in data.index:

            buyPrice = buyFractals[idx]
            sellPrice = sellFractals[idx]

            if buyPrice != lastBuyPrice:
                entities.loc[idx, 'buyFractal'] = buyPrice
            if sellPrice != lastSellPrice:
                entities.loc[idx, 'sellFractal'] = sellPrice

            lastBuyPrice = buyPrice
            lastSellPrice = sellPrice

        fplt.plot(entities['buyFractal'], style='o', color=blue, ax=ax)
        fplt.plot(entities['sellFractal'], style='o', color=aqua, ax=ax)

        # fplt.show()
        return ax