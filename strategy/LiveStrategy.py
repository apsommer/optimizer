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
        self.disableEntryMinutes = params.disableEntryMinutes
        fastMomentumMinutes = params.fastMomentumMinutes
        fastCrossoverPercent = params.fastCrossoverPercent
        takeProfitPercent = params.takeProfitPercent
        fastAngleFactor = params.fastAngleFactor
        slowMinutes = params.slowMinutes
        slowAngleFactor = params.slowAngleFactor
        self.coolOffMinutes = params.coolOffMinutes
        self.positionEntryMinutes = params.positionEntryMinutes

        # convert units, decimal converts int to float
        self.fastAngle = fastAngleFactor / 1000.0
        self.slowAngle = slowAngleFactor / 1000.0
        takeProfit = takeProfitPercent / 100.0

        # calculate fast crossover
        if takeProfit == 0: fastCrossover = fastCrossoverPercent / 100.0
        else: fastCrossover = (fastCrossoverPercent / 100.0) * takeProfit

        # format closing prices
        open_series = pd.Series(data.Open)
        close_series = pd.Series(data.Close)

        # calculate raw averages # todo set min_windows
        self.rawFast = open_series.ewm(span=fastMinutes, adjust=False).mean()
        self.rawSlow = open_series.ewm(span=slowMinutes, adjust=False).mean()
        self.fast = self.rawFast.ewm(span=5, adjust=False).mean()
        self.slow = self.rawSlow.ewm(span=200, adjust=False).mean()
        self.fastSlope = get_slope(self.fast)
        self.slowSlope = get_slope(self.slow)

        self.longExitBarIndex = -1
        self.shortExitBarIndex = -1

        self.isEntryLong = []
        self.isEntryShort = []
        self.entryPrice = []
        self.isEntryLongPyramid = []
        self.isEntryShortPyramid = []
        self.longFastCrossoverExit = []
        self.shortFastCrossoverExit = []
        self.isExitLongFastCrossoverEnabled = []
        self.isExitShortFastCrossoverEnabled = []
        self.isExitLongFastCrossover = []
        self.isExitShortFastCrossover = []
        self.isExitLongFastMomentum = []
        self.isExitShortFastMomentum = []
        self.longTakeProfit = []
        self.shortTakeProfit = []
        self.isExitLongTakeProfit = []
        self.isExitShortTakeProfit = []
        self.isExitLong = []
        self.isExitShort = []

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

        fast = self.fast[idx]
        fastSlope = self.fastSlope[idx]
        fastAngle = self.fastAngle

        slow = self.slow[idx]
        slowSlope = self.slowSlope[idx]
        slowAngle = self.slowAngle

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
        disableEntryMinutes = self.disableEntryMinutes
        if disableEntryMinutes == 0:
            isEntryLongDisabled = False
            isEntryShortDisabled = False
        else:
            recentFastSlope = self.fastSlope[bar_index - disableEntryMinutes : bar_index]
            isEntryLongDisabled = np.min(recentFastSlope) > 0
            isEntryShortDisabled = 0 > np.max(recentFastSlope)

        # enable entry
        positionEntryMinutes = self.positionEntryMinutes
        if positionEntryMinutes == 0:
            isEntryLongEnabled = True
            isEntryShortEnabled = True
        else:
            recentOpen = self.data.Open[bar_index - positionEntryMinutes : bar_index]
            isEntryLongEnabled = fast > np.max(recentOpen)
            isEntryShortEnabled = np.min(recentOpen) > fast

        # short cooloff after trade exit
        coolOffMinutes = self.coolOffMinutes
        longExitBarIndex = self.longExitBarIndex
        shortExitBarIndex = self.shortExitBarIndex
        hasLongEntryDelayElapsed = bar_index - longExitBarIndex > coolOffMinutes
        hasShortEntryDelayElapsed = bar_index - shortExitBarIndex > coolOffMinutes

        # entry long
        if (self.is_flat
            and isFastCrossoverLong
            and not isEntryLongDisabled
            and isEntryLongEnabled
            and slowSlope > slowAngle
            and hasLongEntryDelayElapsed):
                self.buy(self.ticker, self.size, 'long')

        # entry short
        elif (self.is_flat
            and isFastCrossoverShort
            and not isEntryShortDisabled
            and isEntryShortEnabled
            and -slowAngle > slowSlope
            and hasShortEntryDelayElapsed):
                self.sell(self.ticker, self.size, 'short')

        # exit long
        elif self.is_long and bar_index % 987 == 0:
            self.flat(self.ticker, self.size, 'flat')

        # exit short
        elif self.is_short and bar_index % 3109 == 0:
            self.flat(self.ticker, self.size, 'flat')
