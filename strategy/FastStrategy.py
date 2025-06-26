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
        slowAngleFactor = params.slowAngleFactor
        stopAverage = params.stopAverage

        # emas
        fastMinutes = emas.columns[0]
        midMinutes = emas.columns[stopAverage]
        slowMinutes = emas.columns[-1]
        self.fast = emas.loc[:, fastMinutes]
        self.fastSlope = slopes.loc[:, fastMinutes]
        self.mid = emas.loc[:, midMinutes]
        self.midSlope = slopes.loc[:, midMinutes]
        self.slow = emas.loc[:, slowMinutes]
        self.slowSlope = slopes.loc[:, slowMinutes]

        # take profit
        self.takeProfit = takeProfitPercent / 100.0
        self.longTakeProfit = np.nan
        self.shortTakeProfit = np.nan

        # slope threshold
        self.slowAngle = slowAngleFactor / 1000.0

        # track indices
        self.longEntryBarIndex = -1
        self.shortEntryBarIndex = -1
        self.longExitBarIndex = -1
        self.shortExitBarIndex = -1

        self.coolOffMinutes = 120

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

        # emas
        fast = self.fast[idx]
        mid = self.mid[idx]
        slow = self.slow[idx]
        slowSlope = self.slowSlope[idx]

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
        slowAngle = self.slowAngle

        # orders
        ticker = self.ticker
        size = self.size

        ################################################################################################################

        # cooloff after trade exit
        hasLongEntryDelayElapsed = bar_index - self.longExitBarIndex > self.coolOffMinutes
        hasShortEntryDelayElapsed = bar_index - self.shortExitBarIndex > self.coolOffMinutes

        # entry long
        isEntryLong = (
            is_flat
            and slowSlope > slowAngle
            and fast > mid
            and fast > open
            and close > fast
            and close > buyFractal
            and hasLongEntryDelayElapsed
        )
        if isEntryLong:
            self.longEntryBarIndex = bar_index
            self.buy(ticker, size)

        # entry short
        isEntryShort = (
            is_flat
            and -slowAngle > slowSlope
            and mid > fast
            and open > fast
            and fast > close
            and sellFractal > close
            and hasShortEntryDelayElapsed
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

        # exit, crossover regime change
        isExitLongCrossover = is_long and mid > low
        isExitShortCrossover = is_short and high > mid

        # exit, timeout
        isExitLongTimeout = is_long and bar_index - self.longEntryBarIndex > 120
        isExitShortTimeout = is_short and bar_index - self.shortEntryBarIndex > 120

        # exit long
        isExitLong = is_long and (
            isExitLongTakeProfit
            or isExitLongCrossover
            # or isExitLongTimeout
            or self.is_last_bar)
        if isExitLong:
            self.longExitBarIndex = bar_index
            self.flat(ticker, size)

        # exit short
        isExitShort = is_short and (
            isExitShortTakeProfit
            or isExitShortCrossover
            # or isExitShortTimeout
            or self.is_last_bar)
        if isExitShort:
            self.shortExitBarIndex = bar_index
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