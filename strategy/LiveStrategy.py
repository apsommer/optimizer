import numpy as np
import pandas as pd
from strategy.BaseStrategy import BaselineStrategy
from model.Ticker import Ticker
from utils.constants import *
from utils.utils import init_plot
import finplot as fplt
import seaborn as sns
import matplotlib as mpl

class LiveStrategy(BaselineStrategy):

    @property
    def ticker(self):
        return Ticker(
            # symbol = 'NQ',
            symbol = 'MNQ',
            tick_size = 0.25,
            # point_value = 20, # NQ = 20
            point_value = 2, # MNQ = 2
            margin = 0.5) # 10% of underlying, http://tradestation.com/pricing/futures-margin-requirements/

    @property
    def size(self):
        return 1

    def __init__(self, data, emas, fractals, params):
        super().__init__()

        self.data = data
        self.emas = emas
        self.params = params

        # unpack params
        self.fastMinutes = params.fastMinutes
        self.disableEntryMinutes = params.disableEntryMinutes
        self.fastMomentumMinutes = params.fastMomentumMinutes
        fastCrossoverPercent = params.fastCrossoverPercent
        takeProfitPercent = params.takeProfitPercent
        fastAngleFactor = params.fastAngleFactor
        self.slowMinutes = params.slowMinutes
        slowAngleFactor = params.slowAngleFactor
        self.coolOffMinutes = params.coolOffMinutes
        self.trendStartMinutes = params.trendStartHour * 60
        self.trendEndMinutes = params.trendEndHour * 60

        # extract emas
        self.fast = emas.loc[:, 'ema_' + str(self.fastMinutes)]
        self.slow = emas.loc[:, 'ema_' + str(self.slowMinutes)]
        self.fastSlope = emas.loc[:, 'slope_' + str(self.fastMinutes)]
        self.slowSlope = emas.loc[:, 'slope_' + str(self.slowMinutes)]
        self.fastLongMinutes = emas.loc[:, 'long_' + str(self.fastMinutes)]
        self.fastShortMinutes = emas.loc[:, 'short_' + str(self.fastMinutes)]
        self.slowLongMinutes = emas.loc[:, 'long_' + str(self.slowMinutes)]
        self.slowShortMinutes = emas.loc[:, 'short_' + str(self.slowMinutes)]

        # extract fractals
        self.buyFractals = fractals.loc[:, 'buyFractal']
        self.sellFractals = fractals.loc[:, 'sellFractal']

        # convert units
        self.fastAngle = fastAngleFactor / 1000.0
        self.slowAngle = slowAngleFactor / 1000.0
        self.takeProfit = takeProfitPercent / 100.0

        # calculate fast crossover
        if fastCrossoverPercent == 0: self.fastCrossover = 0 # off, tp only
        elif self.takeProfit == 0: self.fastCrossover = fastCrossoverPercent / 100.0 # tp off, fc only
        else: self.fastCrossover = (fastCrossoverPercent / 100.0) * self.takeProfit # both on, fc % of tp

        # strategy
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

        # # todo tradingview limitation ~20k bars
        # tv_start = pd.Timestamp('2025-05-27T18:00:00', tz='America/Chicago')
        # if tv_start > idx:
        #     return

        # params
        fastAngle = self.fastAngle
        slowAngle = self.slowAngle
        disableEntryMinutes = self.disableEntryMinutes
        coolOffMinutes = self.coolOffMinutes
        takeProfit = self.takeProfit

        # data
        open = self.data.Open[idx]
        high = self.data.High[idx]
        low = self.data.Low[idx]
        close = self.data.Close[idx]

        # position
        is_flat = self.is_flat
        is_long = self.is_long
        is_short = self.is_short

        # averages
        fast = self.fast[idx]
        fastSlope = self.fastSlope[idx]
        slow = self.slow[idx]
        slowSlope = self.slowSlope[idx]
        fastLong = self.fastLongMinutes[idx]
        fastShort = self.fastShortMinutes[idx]
        slowLong = self.slowLongMinutes[idx]
        slowShort = self.slowShortMinutes[idx]

        # fractal points
        buyFractal = self.buyFractals[idx]
        sellFractal = self.sellFractals[idx]

        # strategy
        longExitBarIndex = self.longExitBarIndex
        shortExitBarIndex = self.shortExitBarIndex
        fastCrossover = self.fastCrossover
        fastMomentumMinutes = self.fastMomentumMinutes
        longTakeProfit = self.longTakeProfit
        shortTakeProfit = self.shortTakeProfit

        ticker = self.ticker
        size = self.size

        ################################################################################################################

        # disable entry
        if disableEntryMinutes == 0:
            isEntryLongDisabled = False
            isEntryShortDisabled = False
        else:
            isEntryLongDisabled = fastLong > disableEntryMinutes
            isEntryShortDisabled = fastShort > disableEntryMinutes

        # cooloff after trade exit
        hasLongEntryDelayElapsed = bar_index - longExitBarIndex > coolOffMinutes
        hasShortEntryDelayElapsed = bar_index - shortExitBarIndex > coolOffMinutes

        # exit, fast momentum
        if fastMomentumMinutes == 0:
            isExitLongFastMomentum = False
            isExitShortFastMomentum = False

        else:
            isExitLongFastMomentum = (
                is_long
                and fastShort > fastMomentumMinutes)
            isExitShortFastMomentum = (
                is_short
                and fastLong > fastMomentumMinutes)

        # entry long
        isEntryLongSignal = (
            fast > slow
            and not isEntryLongDisabled
            and slowSlope > slowAngle
            and hasLongEntryDelayElapsed
            and self.trendStartMinutes < slowLong < self.trendEndMinutes
            and fast > close > buyFractal > slow
            and 0.5 * fastMomentumMinutes > fastShort
        )

        isEntryLong = (
            ((is_flat or is_short) and isEntryLongSignal)
            or (isExitShortFastMomentum and fast > slow))

        if isEntryLong:
            self.buy(ticker, size)

        # entry short
        isEntryShortSignal = (
            slow > fast
            and not isEntryShortDisabled
            and -slowAngle > slowSlope
            and hasShortEntryDelayElapsed
            and self.trendStartMinutes < slowShort < self.trendEndMinutes
            and slow > sellFractal > close > fast
            and 0.5 * fastMomentumMinutes > fastLong
        )
        isEntryShort = (
            ((is_flat or is_long) and isEntryShortSignal)
            or (isExitLongFastMomentum and slow > fast))
        if isEntryShort:
            self.sell(ticker, size)

        # exit, fast crossover after hitting threshold
        if fastCrossover == 0:

            isExitLongFastCrossover = False
            isExitShortFastCrossover = False

        else:

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

        # exit, take profit
        if takeProfit == 0:
            isExitLongTakeProfit = False
            isExitShortTakeProfit = False

        else:

            if isEntryLong: longTakeProfit = (1 + takeProfit) * fast
            elif not is_long: longTakeProfit = np.nan
            self.longTakeProfit = longTakeProfit
            isExitLongTakeProfit = high > longTakeProfit

            # exit, short take profit:
            if isEntryShort: shortTakeProfit = (1 - takeProfit) * fast
            elif not is_short: shortTakeProfit = np.nan
            self.shortTakeProfit = shortTakeProfit
            isExitShortTakeProfit = shortTakeProfit > low

        # flip
        isExitLongFlip = (is_long and isEntryShortSignal) or (isExitLongFastMomentum and slow > fast)
        isExitShortFlip = (is_short and isEntryLongSignal) or (isExitShortFastMomentum and fast > slow)

        # exit long
        isExitLong = is_long and (
            isExitLongFastCrossover
            or isExitLongFastMomentum
            or isExitLongTakeProfit
            or self.is_last_bar
            or isExitLongFlip
        )
        if isExitLong:

            comment = ''
            if isExitLongFastCrossover: comment = 'fastCrossover'
            elif isExitLongTakeProfit: comment = 'takeProfit'
            elif self.is_last_bar: comment = 'lastBar'

            elif isExitLongFastMomentum and slow > fast: comment = 'flip fastMomentum'
            elif is_long and isEntryShortSignal: comment = 'flip shortSignal'
            elif isExitLongFastMomentum: comment = 'fastMomentum'

            self.longExitBarIndex = bar_index
            self.sell(ticker, size, comment)

        # exit short
        isExitShort = is_short and (
            isExitShortFastCrossover
            or isExitShortFastMomentum
            or isExitShortTakeProfit
            or self.is_last_bar
            or isExitShortFlip
        )
        if isExitShort:

            comment = ''
            if isExitShortFastCrossover: comment = 'fastCrossover'
            elif isExitShortTakeProfit: comment = 'takeProfit'
            elif self.is_last_bar: comment = 'lastBar'

            elif isExitShortFastMomentum and fast > slow: comment = 'flip fastMomentum'
            elif is_short and isEntryLongSignal: comment = 'flip longSignal'
            elif isExitShortFastMomentum: comment = 'fastMomentum'

            self.shortExitBarIndex = bar_index
            self.buy(ticker, size, comment)

    def plot(self, title = 'Strategy', shouldShow = False):

        ax = init_plot(0, title)

        # plot candles
        data = self.data
        fplt.candlestick_ochl(data[['Open', 'Close', 'High', 'Low']], ax=ax, draw_body=False)

        # init dataframe of plot entities
        entities = pd.DataFrame(
            index = data.index,
            dtype = float)

        # fractals
        lastBuyPrice = 0
        lastSellPrice = 0
        for idx in data.index:
            buyPrice = self.buyFractals[idx]
            sellPrice = self.sellFractals[idx]
            if buyPrice != lastBuyPrice:
                entities.loc[idx, 'buyFractal'] = buyPrice
            if sellPrice != lastSellPrice:
                entities.loc[idx, 'sellFractal'] = sellPrice
            lastBuyPrice = buyPrice
            lastSellPrice = sellPrice

        fplt.plot(entities['buyFractal'], style='o', color=blue, ax=ax)
        fplt.plot(entities['sellFractal'], style='o', color=aqua, ax=ax)

        # color ribbon
        crest = sns.color_palette("crest", as_cmap=True)
        ribbon_colors = crest(np.linspace(0, 1, 10))

        # plot ribbon
        ema_columns = [ column for column in self.emas.columns if 'ema' in column ]
        for i, column in enumerate(ema_columns):

            color = mpl.colors.rgb2hex(ribbon_colors[i % 10])
            fplt.plot(self.emas.loc[:, column], color=color, width=2, ax=ax)

        # # emas
        # for idx in data.index:
        #
        #     fast = self.fast[idx]
        #     slow = self.slow[idx]
        #     slowLong = self.slowLongMinutes[idx]
        #     slowShort = self.slowShortMinutes[idx]
        #     slowSlope = self.slowSlope[idx]
        #
        #     if (
        #         fast > slow
        #         and slowSlope > self.slowAngle
        #         and self.trendStartMinutes < slowLong < self.trendEndMinutes):
        #
        #         entities.loc[idx, 'longEnabled'] = slow
        #
        #     elif (
        #         slow > fast
        #         and -self.slowAngle > slowSlope
        #         and self.trendStartMinutes < slowShort < self.trendEndMinutes):
        #
        #         entities.loc[idx, 'shortEnabled'] = slow
        #
        #     else:
        #         entities.loc[idx, 'disabled'] = slow
        #
        # fplt.plot(entities['longEnabled'], style='-', color=blue, ax=ax, width = 10)
        # fplt.plot(entities['shortEnabled'], style='-', color=aqua, ax=ax, width = 10)
        # fplt.plot(entities['disabled'], style='-', color=yellow, ax=ax, width = 1)

        if shouldShow: fplt.show()
        return ax