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

    def __init__(self, data, indicators, params):
        super().__init__()

        self.data = data
        self.params = params

        # unpack params
        fastCrossoverPercent = params.fastCrossoverPercent
        takeProfitPercent = params.takeProfitPercent
        fastAngleFactor = params.fastAngleFactor
        slowAngleFactor = params.slowAngleFactor
        self.coolOffMinutes = params.coolOffMinutes
        self.ratio = params.ratio

        # convert units
        self.fastAngle = fastAngleFactor / 1000.0
        self.slowAngle = slowAngleFactor / 1000.0
        self.takeProfit = takeProfitPercent / 100.0

        # calculate fast crossover
        if fastCrossoverPercent == 0: self.fastCrossover = np.nan # off, tp only
        elif self.takeProfit == 0: self.fastCrossover = fastCrossoverPercent / 100.0 # tp off, fc only
        else: self.fastCrossover = (fastCrossoverPercent / 100.0) * self.takeProfit # both on, fc % of tp

        # get raw averages
        self.fast = indicators.loc[:, 'fast']
        self.slow = indicators.loc[:, 'slow']
        self.fastSlope = indicators.loc[:, 'fastSlope']
        self.slowSlope = indicators.loc[:, 'slowSlope']

        # strategy
        self.longEntryPrice = np.nan
        self.shortEntryPrice = np.nan
        self.longEntryBarIndex = np.nan
        self.shortEntryBarIndex = np.nan
        self.longExitBarIndex = -1
        self.shortExitBarIndex = -1
        self.longFastCrossoverExit = np.nan
        self.shortFastCrossoverExit = np.nan
        self.isExitLongCrossoverEnabled = False
        self.isExitShortCrossoverEnabled = False
        self.longTakeProfit = np.nan
        self.shortTakeProfit = np.nan

    def on_bar(self):

        # index
        idx = self.current_idx
        self.bar_index += 1
        bar_index = self.bar_index

        # params
        fastAngle = self.fastAngle
        slowAngle = self.slowAngle
        coolOffMinutes = self.coolOffMinutes
        takeProfit = self.takeProfit

        # data
        open = self.data.Open[idx]
        high = self.data.High[idx]
        low = self.data.Low[idx]
        close = self.data.Close[idx]
        prev_close = self.data.Close.iloc[bar_index-1]

        # position
        is_flat = self.is_flat
        is_long = self.is_long
        is_short = self.is_short

        # averages
        fast = self.fast[idx]
        fastSlope = self.fastSlope[idx]
        slow = self.slow[idx]
        slowSlope = self.slowSlope[idx]

        # strategy
        longEntryBarIndex = self.longEntryBarIndex
        shortEntryBarIndex = self.shortEntryBarIndex
        longExitBarIndex = self.longExitBarIndex
        shortExitBarIndex = self.shortExitBarIndex
        fastCrossover = self.fastCrossover
        longTakeProfit = self.longTakeProfit
        shortTakeProfit = self.shortTakeProfit
        ratio = self.ratio

        ticker = self.ticker
        size = self.size

        ################################################################################################################

        # entry, long crossover fast
        isFastCrossoverLong = (
            fastSlope > fastAngle
            and (fast > open or fast > prev_close)
            and high > fast)

        # entry, short crossover fast
        isFastCrossoverShort = (
            -fastAngle > fastSlope
            and (open > fast or prev_close > fast)
            and fast > low)

        # cooloff after trade exit
        hasLongEntryDelayElapsed = bar_index - longExitBarIndex > coolOffMinutes
        hasShortEntryDelayElapsed = bar_index - shortExitBarIndex > coolOffMinutes

        # entry long
        isEntryLong = (
            is_flat
            and isFastCrossoverLong
            and slowSlope > slowAngle
            and hasLongEntryDelayElapsed)
        if isEntryLong:
            self.longEntryPrice = close
            self.longEntryBarIndex = bar_index
            self.buy(ticker, size)

        # entry short
        isEntryShort = (
            is_flat
            and isFastCrossoverShort
            and -slowAngle > slowSlope
            and hasShortEntryDelayElapsed)
        if isEntryShort:
            self.shortEntryPrice = close
            self.shortEntryBarIndex = bar_index
            self.sell(ticker, size)

        ################################################################################################################

        # exit, long crossover fast
        longFastCrossoverExit = np.nan
        if isEntryLong: longFastCrossoverExit = (1 + fastCrossover) * fast
        elif is_long: longFastCrossoverExit = self.longFastCrossoverExit
        self.longFastCrossoverExit = longFastCrossoverExit

        if not is_long: isExitLongCrossoverEnabled = False
        elif self.isExitLongCrossoverEnabled: isExitLongCrossoverEnabled = True
        else: isExitLongCrossoverEnabled = high > longFastCrossoverExit
        self.isExitLongCrossoverEnabled = isExitLongCrossoverEnabled

        isExitLongFastCrossover =(
            isExitLongCrossoverEnabled
            and fast > low)

        # exit, short crossover fast
        shortFastCrossoverExit = np.nan
        if isEntryShort: shortFastCrossoverExit = (1 - fastCrossover) * fast
        elif is_short: shortFastCrossoverExit = self.shortFastCrossoverExit
        self.shortFastCrossoverExit = shortFastCrossoverExit

        if not is_short: isExitShortCrossoverEnabled = False
        elif self.isExitShortCrossoverEnabled: isExitShortCrossoverEnabled = True
        else: isExitShortCrossoverEnabled = shortFastCrossoverExit > low
        self.isExitShortCrossoverEnabled = isExitShortCrossoverEnabled

        isExitShortFastCrossover = (
            isExitShortCrossoverEnabled
            and high > fast)

        # exit, long take profit
        if isEntryLong: longTakeProfit = (1 + takeProfit) * fast
        elif not is_long: longTakeProfit = np.nan
        self.longTakeProfit = longTakeProfit
        isExitLongTakeProfit = high > longTakeProfit

        # exit, short take profit:
        if isEntryShort: shortTakeProfit = (1 - takeProfit) * fast
        elif not is_short: shortTakeProfit = np.nan
        self.shortTakeProfit = shortTakeProfit
        isExitShortTakeProfit = shortTakeProfit > low

        # exit on last bar of data, prevent last trade open
        isExitLastBar = False
        if idx == self.data.index[-1]:
            if is_long or is_short:
                isExitLastBar = True

        # todo exit
        hasLongTradeElapsed = (
            is_long
            and bar_index - longEntryBarIndex > 15
            and (1 - ratio * takeProfit) * self.longEntryPrice > close
        )
        hasShortTradeElapsed = (
            is_short
            and bar_index - shortEntryBarIndex > 15
            and close > (1 + ratio * takeProfit) * self.shortEntryPrice
        )

        # exit long
        isExitLong = (
            isExitLongFastCrossover
            or hasLongTradeElapsed
            or isExitLongTakeProfit
            or isExitLastBar)
        if isExitLong:
            self.longExitBarIndex = bar_index
            self.flat(ticker, size)

        # exit short
        isExitShort = (
            isExitShortFastCrossover
            or hasShortTradeElapsed
            or isExitShortTakeProfit
            or isExitLastBar)
        if isExitShort:
            self.shortExitBarIndex = bar_index
            self.flat(ticker, size)

    def plot(self):

        ax = init_plot(0, 'Strategy')

        # candlestick ohlc
        data = self.data
        fplt.candlestick_ochl(data[['Open', 'Close', 'High', 'Low']], ax=ax, draw_body=False, draw_shadow=False)

        # build enabled long, short, and disabled
        fast = self.fast
        fastSlope = self.fastSlope
        fastAngle = self.fastAngle
        slow = self.slow
        slowSlope = self.slowSlope
        slowAngle = self.slowAngle

        # init containers of nan
        fast_df = pd.DataFrame(
            data=np.full([len(data), 3], np.nan),
            columns=['long_enabled', 'short_enabled', 'disabled'],
            index=data.index)
        slow_df = fast_df.copy()

        prev_idx = data.index[0]
        for idx in data.index:

            # slow
            is_slow_long_enabled = slowSlope[idx] > slowAngle or slowSlope[prev_idx] > slowAngle
            is_slow_short_enabled = -slowAngle > slowSlope[idx] or -slowAngle > slowSlope[prev_idx]
            is_slow_disabled = -slowAngle < slowSlope[idx] < slowAngle or -slowAngle < slowSlope[prev_idx] < slowAngle

            if is_slow_long_enabled: slow_df.loc[idx, 'long_enabled'] = slow[idx]
            if is_slow_short_enabled: slow_df.loc[idx, 'short_enabled'] = slow[idx]
            if is_slow_disabled: slow_df.loc[idx, 'disabled'] = slow[idx]

            # fast
            is_fast_long_enabled = fastSlope[idx] > fastAngle or fastSlope[prev_idx] > fastAngle
            is_fast_short_enabled = -fastAngle > fastSlope[idx] or -fastAngle > fastSlope[prev_idx]
            is_fast_disabled = -fastAngle < fastSlope[idx] < fastAngle or -fastAngle < fastSlope[prev_idx] < fastAngle

            if is_fast_long_enabled: fast_df.loc[idx, 'long_enabled'] = fast[idx]
            if is_fast_short_enabled: fast_df.loc[idx, 'short_enabled'] = fast[idx]
            if is_fast_disabled: fast_df.loc[idx, 'disabled'] = fast[idx]

            prev_idx = idx

        # overlay slow
        fplt.plot(slow_df['long_enabled'], color=blue, width=2, ax=ax)
        fplt.plot(slow_df['short_enabled'], color=aqua, width=2, ax=ax)
        fplt.plot(slow_df['disabled'], color=gray, width=2, ax=ax)

        # overlay fast
        fplt.plot(fast_df['long_enabled'], color=green, width=2, ax=ax)
        fplt.plot(fast_df['short_enabled'], color=red, width=2, ax=ax)
        fplt.plot(fast_df['disabled'], color=gray, width=2, ax=ax)

        fplt.show()