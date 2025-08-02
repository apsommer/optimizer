import finplot as fplt
import pandas as pd

from model.Ticker import Ticker
from strategy.BaseStrategy import BaselineStrategy
from utils.constants import *
from utils.utils import init_plot

class LiveStrategy(BaselineStrategy):

    # margin 10% of underlying, http://tradestation.com/pricing/futures-margin-requirements/
    @property
    def ticker(self):
        return Ticker(
            symbol = 'MES',
            point_value = 5,
            tick_size = 0.25,
            margin = 0.5
        )

    @property
    def size(self):
        return 1

    def __init__(self, data, emas, fractals, params):
        super().__init__()

        self.data = data
        self.emas = emas
        self.params = params

        # allow blank strategy for walk-forward composite
        if params is None: return

        # unpack params
        self.fastMinutes = params.fastMinutes
        self.disableEntryMinutes = params.disableEntryMinutes
        self.fastMomentumMinutes = params.fastMomentumMinutes
        fastCrossoverPercent = params.fastCrossoverPercent
        takeProfitPercent = params.takeProfitPercent
        stopLossPercent = params.stopLossPercent
        fastAngleEntryFactor = params.fastAngleEntryFactor
        fastAngleExitFactor = params.fastAngleExitFactor
        self.slowMinutes = params.slowMinutes
        slowAngleFactor = params.slowAngleFactor
        self.coolOffMinutes = params.coolOffMinutes
        self.trendStartMinutes = params.trendStartHour * 60
        self.trendEndMinutes = params.trendEndHour * 60

        # exponential moving averages
        self.fast = emas.loc[:, 'ema_' + str(self.fastMinutes)]
        self.fastSlope = emas.loc[:, 'slope_' + str(self.fastMinutes)]
        self.fastLongMinutes = emas.loc[:, 'long_' + str(self.fastMinutes)]
        self.fastShortMinutes = emas.loc[:, 'short_' + str(self.fastMinutes)]

        self.slow = emas.loc[:, 'ema_' + str(self.slowMinutes)]
        self.slowSlope = emas.loc[:, 'slope_' + str(self.slowMinutes)]
        self.slowLongMinutes = emas.loc[:, 'long_' + str(self.slowMinutes)]
        self.slowShortMinutes = emas.loc[:, 'short_' + str(self.slowMinutes)]

        # fractals
        self.buyFractals = fractals.loc[:, 'buyFractal']
        self.sellFractals = fractals.loc[:, 'sellFractal']

        # units
        self.fastAngleEntry = fastAngleEntryFactor / 1000.0
        self.fastAngleExit = fastAngleExitFactor / 1000.0
        self.slowAngle = slowAngleFactor / 1000.0
        self.takeProfit = takeProfitPercent / 100.0
        self.stopLoss = stopLossPercent / 100.0

        # calculate fast crossover
        if fastCrossoverPercent == 0: self.fastCrossover = 0 # disable
        elif self.takeProfit == 0: self.fastCrossover = fastCrossoverPercent / 100.0 # crossover only, disable take profit
        else: self.fastCrossover = (fastCrossoverPercent / 100.0) * self.takeProfit # crossover = % of take profit

        # strategy
        self.longExitBarIndex = -1
        self.shortExitBarIndex = -1
        self.longFastCrossoverExit = np.nan
        self.shortFastCrossoverExit = np.nan
        self.isExitLongCrossoverEnabled = False
        self.isExitShortCrossoverEnabled = False
        self.longTakeProfit = np.nan
        self.shortTakeProfit = np.nan
        self.longStopLoss = np.nan
        self.shortStopLoss = np.nan

    def on_bar(self):

        # index
        idx = self.current_idx
        self.bar_index += 1
        bar_index = self.bar_index

        # params
        fastAngleEntry = self.fastAngleEntry
        fastAngleExit = self.fastAngleExit
        slowAngle = self.slowAngle
        disableEntryMinutes = self.disableEntryMinutes
        coolOffMinutes = self.coolOffMinutes
        takeProfit = self.takeProfit
        stopLoss = self.stopLoss

        # data
        open = self.data.Open[idx]
        high = self.data.High[idx]
        low = self.data.Low[idx]
        close = self.data.Close[idx]

        # averages
        fast = self.fast[idx]
        fastSlope = self.fastSlope[idx]
        fastLong = self.fastLongMinutes[idx]
        fastShort = self.fastShortMinutes[idx]

        slow = self.slow[idx]
        slowSlope = self.slowSlope[idx]
        slowLong = self.slowLongMinutes[idx]
        slowShort = self.slowShortMinutes[idx]

        # fractal
        buyFractal = self.buyFractals[idx]
        sellFractal = self.sellFractals[idx]

        # strategy
        longExitBarIndex = self.longExitBarIndex
        shortExitBarIndex = self.shortExitBarIndex
        fastCrossover = self.fastCrossover
        fastMomentumMinutes = self.fastMomentumMinutes
        longTakeProfit = self.longTakeProfit
        shortTakeProfit = self.shortTakeProfit
        longStopLoss = self.longStopLoss
        shortStopLoss = self.shortStopLoss

        # position
        ticker = self.ticker
        size = self.size
        is_flat = self.is_flat
        is_long = self.is_long
        is_short = self.is_short

        ################################################################################################################

        # disable entry after fast trends in 1 direction for certain time
        if disableEntryMinutes == 0:
            isEntryLongDisabled = False
            isEntryShortDisabled = False
        else:
            isEntryLongDisabled = fastLong > disableEntryMinutes
            isEntryShortDisabled = fastShort > disableEntryMinutes

        # cooloff time imposed after trade exit
        hasLongEntryDelayElapsed = bar_index - longExitBarIndex > coolOffMinutes
        hasShortEntryDelayElapsed = bar_index - shortExitBarIndex > coolOffMinutes

        # exit, slow momentum drift against trade position
        if fastMomentumMinutes == 0:
            isExitLongFastMomentum = False
            isExitShortFastMomentum = False
        else:
            isExitLongFastMomentum = (
                is_long
                and fastShort > fastMomentumMinutes
            )
            isExitShortFastMomentum = (
                is_short
                and fastLong > fastMomentumMinutes
            )

        # exit, rapid momentum swing
        if fastAngleExit == 0:
            isExitLongRapidMomentum = False
            isExitShortRapidMomentum = False
        else:
            isExitLongRapidMomentum = is_long and -fastAngleExit > fastSlope
            isExitShortRapidMomentum = is_short and fastSlope > fastAngleExit

        # entry, long fractal signal
        isEntryLongFractal = (
            fast > slow
            and not isEntryLongDisabled
            and slowSlope > slowAngle
            and self.trendStartMinutes < slowLong < self.trendEndMinutes
            and fast > close > buyFractal > slow
            and 0.5 * fastMomentumMinutes > fastShort
        )

        # entry, long fast crossover todo creates too many trades?
        isEntryLongFastCrossover = (
            high > fast > open
            and fastSlope > fastAngleEntry
            and fast > slow
            and slowSlope > slowAngle
        )

        # entry, long
        isEntryLongSignal = isEntryLongFractal or isEntryLongFastCrossover
        isEntryLong = (
            hasLongEntryDelayElapsed and (
                ((is_flat or is_short) and isEntryLongSignal)
                or (isExitShortFastMomentum and fast > slow)
                or (isExitShortRapidMomentum and fast > slow)))
        if isEntryLong:
            self.buy(ticker, size)

        # entry, short fractal signal
        isEntryShortFractal = (
            slow > fast
            and not isEntryShortDisabled
            and -slowAngle > slowSlope
            and self.trendStartMinutes < slowShort < self.trendEndMinutes
            and slow > sellFractal > close > fast
            and 0.5 * fastMomentumMinutes > fastLong
        )

        # entry, short fast crossover
        isEntryShortFastCrossover = (
            open > fast > low
            and -fastAngleEntry > fastSlope
            and slow > fast
            and -slowAngle > slowSlope
        )

        # entry, short
        isEntryShortSignal =  isEntryShortFractal or isEntryShortFastCrossover
        isEntryShort = (
            hasShortEntryDelayElapsed and (
                ((is_flat or is_long) and isEntryShortSignal)
                or (isExitLongFastMomentum and slow > fast
                or (isExitLongRapidMomentum and slow > fast))))
        if isEntryShort:
            self.sell(ticker, size)

        # exit, fast crossover after hitting threshold
        if fastCrossover == 0:
            isExitLongFastCrossover = False
            isExitShortFastCrossover = False

        else:

            longFastCrossoverExit = np.nan
            if isEntryLong: longFastCrossoverExit = (1 + fastCrossover) * close
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
            if isEntryShort: shortFastCrossoverExit = (1 - fastCrossover) * close
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

            if isEntryLong: longTakeProfit = (1 + takeProfit) * close
            elif not is_long: longTakeProfit = np.nan
            self.longTakeProfit = longTakeProfit
            isExitLongTakeProfit = high > longTakeProfit

            if isEntryShort: shortTakeProfit = (1 - takeProfit) * close
            elif not is_short: shortTakeProfit = np.nan
            self.shortTakeProfit = shortTakeProfit
            isExitShortTakeProfit = shortTakeProfit > low

        # exit, stop loss
        if stopLoss == 0:
            isExitLongStopLoss = False
            isExitShortStopLoss = False

        else:

            if isEntryLong: longStopLoss = (1 - stopLoss) * close
            elif not is_long: longStopLoss = np.nan
            self.longStopLoss = longStopLoss
            isExitLongStopLoss = longStopLoss > low

            if isEntryShort: shortStopLoss = (1 + stopLoss) * close
            elif not is_short: shortStopLoss = np.nan
            self.shortStopLoss = shortStopLoss
            isExitShortStopLoss = high > shortStopLoss

        # flip trade immediately in opposite direction
        isExitLongFlip = (
            (is_long and isEntryShortSignal)
            or (isExitLongFastMomentum and slow > fast)
            or (isExitLongRapidMomentum and slow > fast))
        isExitShortFlip = (
            (is_short and isEntryLongSignal)
            or (isExitShortFastMomentum and fast > slow)
            or (isExitShortRapidMomentum and fast > slow))

        # exit long
        isExitLong = is_long and (
            isExitLongFastCrossover
            or isExitLongFastMomentum
            or isExitLongTakeProfit
            or isExitLongStopLoss
            or self.is_last_bar
            or isExitLongFlip
            or isExitLongRapidMomentum
        )

        if isExitLong:

            comment = ''
            if isExitLongFastCrossover: comment = 'fastCrossover'
            elif isExitLongTakeProfit: comment = 'takeProfit'
            elif self.is_last_bar: comment = 'lastBar'
            elif isExitLongFastMomentum and slow > fast: comment = 'flip fastMomentum'
            elif is_long and isEntryShortSignal: comment = 'flip shortSignal'
            elif isExitLongRapidMomentum and slow > fast: comment = 'flip rapidMomentum'
            elif isExitLongFastMomentum: comment = 'fastMomentum'
            elif isExitLongStopLoss: comment = 'stopLoss'
            elif isExitLongRapidMomentum: comment = 'rapidMomentum'

            self.longExitBarIndex = bar_index
            self.sell(ticker, size, comment)

        # exit short
        isExitShort = is_short and (
            isExitShortFastCrossover
            or isExitShortFastMomentum
            or isExitShortTakeProfit
            or isExitShortStopLoss
            or self.is_last_bar
            or isExitShortFlip
            or isExitShortRapidMomentum
        )

        if isExitShort:

            comment = ''
            if isExitShortFastCrossover: comment = 'fastCrossover'
            elif isExitShortTakeProfit: comment = 'takeProfit'
            elif self.is_last_bar: comment = 'lastBar'
            elif isExitShortFastMomentum and fast > slow: comment = 'flip fastMomentum'
            elif is_short and isEntryLongSignal: comment = 'flip longSignal'
            elif isExitShortRapidMomentum and fast > slow: comment = 'flip rapidMomentum'
            elif isExitShortFastMomentum: comment = 'fastMomentum'
            elif isExitShortStopLoss: comment = 'stopLoss'
            elif isExitShortRapidMomentum: comment = 'rapidMomentum'

            self.shortExitBarIndex = bar_index
            self.buy(ticker, size, comment)

    ####################################################################################################################

    def plot(self, window, title ='Strategy', shouldShow = False):

        ax = init_plot(
            window= window,
            title = title)

        # plot candles
        data = self.data
        fplt.candlestick_ochl(data[['Open', 'Close', 'High', 'Low']], ax=ax, draw_body=False)

        # init dataframe of plot entities
        entities = pd.DataFrame(
            index = data.index,
            dtype = float)

        # plot fractals
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

        # plot ribbon
        ema_columns = [ column for column in self.emas.columns if 'ema' in column ]
        for i, column in enumerate(ema_columns):

            fplt.plot(
                self.emas.loc[:, column],
                color = get_ribbon_color(i),
                width = i,
                ax = ax)

        if shouldShow: fplt.show()
        return ax