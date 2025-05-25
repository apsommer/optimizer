import numpy as np
import pandas as pd
from strategy.BaselineStrategy import BaselineStrategy
from model.Ticker import Ticker
from strategy.LiveUtils import get_slope

class LiveStrategy(BaselineStrategy):

    def __init__(self, data, params):
        super().__init__()

        self.data = data
        self.params = params

        # unpack params
        fastMinutes = params.fastMinutes
        slowMinutes = params.slowMinutes
        fastAngleFactor = params.fastAngleFactor
        slowAngleFactor = params.slowAngleFactor
        fastCrossoverPercent = params.fastCrossoverPercent
        takeProfitPercent = params.takeProfitPercent

        self.disableEntryMinutes = params.disableEntryMinutes
        self.fastMomentumMinutes = params.fastMomentumMinutes
        self.coolOffMinutes = params.coolOffMinutes
        self.positionEntryMinutes = params.positionEntryMinutes

        # convert units, decimal converts int to float
        self.fastAngle = fastAngleFactor / 1000.0
        self.slowAngle = slowAngleFactor / 1000.0
        self.takeProfit = takeProfitPercent / 100.0

        # calculate fast crossover
        if self.takeProfit == 0: self.fastCrossover = fastCrossoverPercent / 100.0
        else: self.fastCrossover = (fastCrossoverPercent / 100.0) * self.takeProfit

        # calculate raw averages # todo set min_windows
        self.rawFast = pd.Series(data.Open).ewm(span=fastMinutes, adjust=False).mean()
        self.rawSlow = pd.Series(data.Open).ewm(span=slowMinutes, adjust=False).mean()
        self.fast = self.rawFast.ewm(span=5, adjust=False).mean()
        self.slow = self.rawSlow.ewm(span=200, adjust=False).mean()
        self.fastSlope = get_slope(self.fast)
        self.slowSlope = get_slope(self.slow)

        self.longExitBarIndex = -1
        self.shortExitBarIndex = -1
        self.longFastCrossoverExit = np.nan
        self.shortFastCrossoverExit = np.nan
        self.longTakeProfit = np.nan
        self.shortTakeProfit = np.nan

    @property
    def ticker(self):
        return Ticker(
            symbol = 'MNQ',
            tick_value = 0.50,
            margin = 0.10) # 10% of underlying, http://tradestation.com/pricing/futures-margin-requirements/

    @property
    def size(self):
        return 1

    def on_bar(self):

        self.bar_index += 1
        bar_index = self.bar_index
        idx = self.current_idx

        open = self.data.Open[idx]
        high = self.data.High[idx]
        low = self.data.Low[idx]
        close = self.data.Close[idx]
        prev_close = self.data.Close.iloc[bar_index-1]

        is_flat = self.is_flat
        is_long = self.is_long
        is_short = self.is_short

        fast = self.fast[idx]
        fastSlope = self.fastSlope[idx]
        fastAngle = self.fastAngle

        slow = self.slow[idx]
        slowSlope = self.slowSlope[idx]
        slowAngle = self.slowAngle

        disableEntryMinutes = self.disableEntryMinutes
        positionEntryMinutes = self.positionEntryMinutes
        coolOffMinutes = self.coolOffMinutes
        longExitBarIndex = self.longExitBarIndex
        shortExitBarIndex = self.shortExitBarIndex
        fastCrossover = self.fastCrossover
        longFastCrossoverExit = self.longFastCrossoverExit
        shortFastCrossoverExit = self.shortFastCrossoverExit
        fastMomentumMinutes = self.fastMomentumMinutes
        takeProfit = self.takeProfit
        longTakeProfit = self.longTakeProfit
        shortTakeProfit = self.shortTakeProfit

        # crossover fast
        isFastCrossoverLong = (
            fastSlope > fastAngle
            and (fast > open or fast > prev_close)
            and high > fast)
        isFastCrossoverShort = (
            -fastAngle > fastSlope
            and (open > fast or prev_close > fast)
            and fast > low)

        # disable entry
        if disableEntryMinutes == 0:
            isEntryLongDisabled = False
            isEntryShortDisabled = False
        else:
            recentFastSlope = self.fastSlope[bar_index - disableEntryMinutes : bar_index]
            isEntryLongDisabled = np.min(recentFastSlope) > 0
            isEntryShortDisabled = 0 > np.max(recentFastSlope)

        # enable entry
        if positionEntryMinutes == 0:
            isEntryLongEnabled = True
            isEntryShortEnabled = True
        else:
            recentOpen = self.data.Open[bar_index - positionEntryMinutes : bar_index]
            isEntryLongEnabled = fast > np.max(recentOpen)
            isEntryShortEnabled = np.min(recentOpen) > fast

        # cooloff after trade exit
        hasLongEntryDelayElapsed = bar_index - longExitBarIndex > coolOffMinutes
        hasShortEntryDelayElapsed = bar_index - shortExitBarIndex > coolOffMinutes

        # entry long
        isEntryLong = (is_flat
            and isFastCrossoverLong
            and not isEntryLongDisabled
            and isEntryLongEnabled
            and slowSlope > slowAngle
            and hasLongEntryDelayElapsed)
        if isEntryLong:
            self.buy(self.ticker, self.size, 'long')

        # entry short
        isEntryShort = (
            is_flat
            and isFastCrossoverShort
            and not isEntryShortDisabled
            and isEntryShortEnabled
            and -slowAngle > slowSlope
            and hasShortEntryDelayElapsed)
        if isEntryShort:
            self.sell(self.ticker, self.size, 'short')

        # exit long fast crossover
        if fastCrossover == 0 or not is_long: longFastCrossoverExit = np.nan
        elif isEntryLong: longFastCrossoverExit = (1 + fastCrossover) * fast
        self.longFastCrossoverExit = longFastCrossoverExit

        isExitLongFastCrossover = (
            high > longFastCrossoverExit
            and fast > low)

        # exit short fast crossover
        if fastCrossover == 0 or not is_short: shortFastCrossoverExit = np.nan
        elif isEntryShort: shortFastCrossoverExit = (1 - fastCrossover) * fast
        self.shortFastCrossoverExit = shortFastCrossoverExit

        isExitShortFastCrossover = (
            shortFastCrossoverExit > low
            and high > fast)

        # exit fast momentum, ouch
        recentSlope = self.fastSlope[bar_index - fastMomentumMinutes : bar_index]
        isExitLongFastMomentum = is_long and -fastAngle > np.max(recentSlope)
        isExitShortFastMomentum = is_short and np.min(recentSlope) > fastAngle

        # exit long take profit
        if not is_long: longTakeProfit = np.nan
        elif isEntryLong: longTakeProfit = (1 + takeProfit) * fast
        self.longTakeProfit = longTakeProfit
        isExitLongTakeProfit = high > longTakeProfit

        # exit short take profit:
        if not is_short: shortTakeProfit = np.nan
        elif isEntryShort: shortTakeProfit = (1 - takeProfit) * fast
        self.shortTakeProfit = shortTakeProfit
        isExitShortTakeProfit = shortTakeProfit > low

        # exit long
        isExitLong = (
            isExitLongFastCrossover
            or isExitLongFastMomentum
            or isExitLongTakeProfit)
        if isExitLong:
            self.longExitBarIndex = bar_index
            self.flat(self.ticker, self.size, 'flat')

        # exit short
        isExitShort = (
            isExitShortFastCrossover
            or isExitShortFastMomentum
            or isExitShortTakeProfit)
        if isExitShort:
            self.shortExitBarIndex = bar_index
            self.flat(self.ticker, self.size, 'flat')
