import pandas as pd

from strategy.BaselineStrategy import BaselineStrategy
from model.Ticker import Ticker

class LiveStrategy(BaselineStrategy):

    def __init__(self):
        super().__init__()

        fastMinutes = 25
        disableEntryMinutes = 105
        fastMomentumMinutes = 135
        fastCrossoverPercent = 0
        takeProfitPercent = 0.35
        fastAngleFactor = 15
        slowMinutes = 2355
        slowAngleFactor = 20
        entryRestriction_minutes = 0
        entryRestriction_percent = 0

        coolOffMinutes = 5
        positionEntryMinutes = 1

        # convert units, decimal converts int to float
        fastAngle = fastAngleFactor / 1000.0
        slowAngle = slowAngleFactor / 1000.0
        takeProfit = takeProfitPercent / 100.0

        # calculate fast crossover
        if takeProfit == 0: fastCrossover = fastCrossoverPercent / 100.0
        else: fastCrossover = (fastCrossoverPercent / 100.0) * takeProfit

        # format closing prices
        open_df = pd.DataFrame({'open': self.data.Open})
        open_series = pd.Series(open_df['open'])
        close_df = pd.DataFrame({'close': self.data.Close})
        close_series = pd.Series(close_df['close'])

        # calculate raw averages # todo set min_windows
        self.rawFast = open_series.ewm(span=fastMinutes, adjust=False).mean()
        self.rawSlow = open_series.ewm(span=slowMinutes, adjust=False).mean()
        self.fast = self.rawFast.ewm(span=5, adjust=False).mean()
        self.slow = self.rawSlow.ewm(span=200, adjust=False).mean()
        
        self.fastSlope = []
        self.slowSlope = []
        self.slowPositiveBarIndex = []
        self.slowNegativeBarIndex = []
        self.isFastCrossoverLong = []
        self.isFastCrossoverShort = []
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
        idx = self.current_idx














        # entry long
        if self.is_flat and self.bar_index % 321 == 0:
            self.buy(self.ticker, self.size, 'long')

        # exit long
        elif self.is_long and self.bar_index % 987 == 0:
            self.flat(self.ticker, self.size, 'flat')

        # entry short
        elif self.is_flat and self.bar_index % 1113 == 0:
            self.sell(self.ticker, self.size, 'short')

        # exit short
        elif self.is_short and self.bar_index % 3109 == 0:
            self.flat(self.ticker, self.size, 'flat')
