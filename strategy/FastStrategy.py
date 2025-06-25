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
        stopLossPercent = params.stopLossPercent
        slowAngleFactor = params.slowAngleFactor

        self.takeProfit = takeProfitPercent / 100.0
        self.longTakeProfit = np.nan
        self.shortTakeProfit = np.nan

        self.stopLoss = stopLossPercent / 100.0
        self.longStopLoss = np.nan
        self.shortStopLoss = np.nan

        self.slowAngle = slowAngleFactor / 1000.0

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

        # fastest and slowest average
        fastestEma = emas.loc[idx, 60]
        fastestSlope = slopes.loc[idx, 60]
        slowestEma = emas.loc[idx, 3000]
        slowestSlope = slopes.loc[idx, 3000]

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
        stopLoss = self.stopLoss
        longStopLoss = self.longStopLoss
        shortStopLoss = self.shortStopLoss
        isExitLastBar = False
        slowAngle = self.slowAngle

        # orders
        ticker = self.ticker
        size = self.size

        ################################################################################################################

        # entry long
        isEntryLong = (
                is_flat
                and slowestEma < open < fastestEma
                and close > buyFractal
                and close > fastestEma
                and buyFractal > fastestEma
                and slowestSlope > slowAngle
        )
        if isEntryLong:
            self.buy(ticker, size)

        # entry short
        isEntryShort = (
                is_flat
                and slowestEma > open > fastestEma
                and sellFractal > close
                and fastestEma > close
                and fastestEma > sellFractal
                and -slowAngle > slowestSlope
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

        # exit, long momentum
        isExitLongMomentum = is_long and -slowAngle > slowestSlope
        isExitShortMomentum = is_short and slowestSlope > slowAngle

        # exit, crossover regime change
        isExitLongCrossover = is_long and close > fastestEma
        isExitShortCrossover = is_short and fastestEma > close

        # exit on last bar of data
        if idx == self.data.index[-1]:
            if is_long or is_short:
                isExitLastBar = True

        # exit long
        isExitLong = is_long and (
               isExitLongTakeProfit
            or isExitLongStopLoss
            or isExitLongMomentum
            or isExitLongCrossover
            or isExitLastBar)
        if isExitLong:
            self.flat(ticker, size)

        # exit short
        isExitShort = is_short and (
               isExitShortTakeProfit
            or isExitShortStopLoss
            or isExitShortMomentum
            or isExitShortCrossover
            or isExitLastBar)
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
            color = mpl.colors.rgb2hex(colors[i])
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