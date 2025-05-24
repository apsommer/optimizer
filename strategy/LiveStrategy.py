import numpy as np
import pandas as pd
from sympy.codegen.ast import continue_
from sympy.physics.quantum.gate import normalized

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
        disableEntryMinutes = params.disableEntryMinutes
        fastMomentumMinutes = params.fastMomentumMinutes
        fastCrossoverPercent = params.fastCrossoverPercent
        takeProfitPercent = params.takeProfitPercent
        fastAngleFactor = params.fastAngleFactor
        slowMinutes = params.slowMinutes
        slowAngleFactor = params.slowAngleFactor
        coolOffMinutes = params.coolOffMinutes
        positionEntryMinutes = params.positionEntryMinutes

        # convert units, decimal converts int to float
        self.fastAngle = fastAngleFactor / 1000.0
        slowAngle = slowAngleFactor / 1000.0
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

        self.isEntryDisabled = []
        self.isEntryLongDisabled = []
        self.isEntryShortDisabled = []
        self.hasLongEntryDelayElapsed = []
        self.hasShortEntryDelayElapsed = []
        self.isEntryLongEnabled = []
        self.isEntryShortEnabled = []
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
        self.longExitBarIndex = []
        self.shortExitBarIndex = []

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

        isFastCrossoverLong = (
            fastSlope > fastAngle
            and (fast > open or fast > prev_close)
            and high > fast)
        isFastCrossoverShort = (
            -fastAngle > fastSlope
            and (open > fast or prev_close > fast)
            and fast > low)

        # entry long
        if self.is_flat and bar_index % 321 == 0:
            self.buy(self.ticker, self.size, 'long')

        # exit long
        elif self.is_long and bar_index % 987 == 0:
            self.flat(self.ticker, self.size, 'flat')

        # entry short
        elif self.is_flat and bar_index % 1113 == 0:
            self.sell(self.ticker, self.size, 'short')

        # exit short
        elif self.is_short and bar_index % 3109 == 0:
            self.flat(self.ticker, self.size, 'flat')
