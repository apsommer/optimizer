import numpy as np
import pandas as pd
import finplot as fplt
from tqdm import tqdm

from analysis.Engine import Engine
from model.Fitness import Fitness
from strategy.LiveStrategy import LiveStrategy
from utils.constants import *
from utils.metrics import *
from utils.utils import *

def init_plot(id):

    # window position, maximized
    fplt.winx = id * 3840
    fplt.winy = 0
    fplt.winw = 3840
    fplt.winh = 2160

    # background todo font size
    fplt.background = light_black
    fplt.candle_bull_color = light_gray
    fplt.candle_bull_body_color = light_gray
    fplt.candle_bear_color = dark_gray
    fplt.candle_bear_body_color = dark_gray
    fplt.cross_hair_color = white

    # init finplot
    ax = fplt.create_plot(title='Equity')

    # axis
    axis_pen = fplt._makepen(color = gray)
    ax.axes['right']['item'].setPen(axis_pen)
    ax.axes['right']['item'].setTextPen(axis_pen)
    ax.axes['right']['item'].setTickPen(None)
    ax.axes['bottom']['item'].setPen(axis_pen)
    ax.axes['bottom']['item'].setTextPen(axis_pen)
    ax.axes['bottom']['item'].setTickPen(None)

    # crosshair
    ax.crosshair.vline.setPen(axis_pen)
    ax.crosshair.hline.setPen(axis_pen)

    return ax

def plot_equity(wfa):

    ax = init_plot(0)

    for fitness in Fitness:

        # rebuild composite OS engine
        result = unpack(fitness.value, wfa.path[:-1])
        params = result['params']
        cash_series = result['cash_series']

        # create strategy, engine
        start = cash_series.index[0]
        end = cash_series.index[-1]
        comp = wfa.data[start:end]

        strategy = LiveStrategy(comp, wfa.avgs, params)
        engine = Engine(fitness.value, strategy)

        # deserialize previous result
        engine.id = result['id']
        engine.params = params
        engine.metrics = result['metrics']
        engine.trades = result['trades']
        engine.cash_series = cash_series
        engine.cash = cash_series[-1]

        # plot selected fitness composite
        if fitness is wfa.best_fitness:
            print_metrics(engine.metrics)
            engine.print_trades()
            plot_trades(engine)

        # plot cash series
        fplt.plot(cash_series, color = fitness.color, legend = fitness.pretty, ax = ax)

        # only calc once
        if fitness is Fitness.PROFIT:

            # plot initial cash
            fplt.plot(engine.initial_cash, color=dark_gray, ax=ax)

            # reference simple buy and hold
            size = engine.strategy.size
            point_value = engine.strategy.ticker.point_value
            delta_df = engine.data.Close - engine.data.Close.iloc[0]
            initial_cash = engine.initial_cash
            buy_hold = size * point_value * delta_df + initial_cash

            # plot buy and hold
            fplt.plot(buy_hold, color=dark_gray, ax=ax)

    fplt.show()

def plot_trades(engine):

    ax = init_plot(1)

    # candlestick ohlc
    data = engine.data
    fplt.candlestick_ochl(
        data[['Open', 'Close', 'High', 'Low']],
        ax = ax) #, draw_body=False, draw_shadow=False)

    # cloud
    # low = fplt.plot(data.Low, color=black, width=0, ax=ax)
    # high = fplt.plot(data.High, color=black, width=0, ax=ax)
    # fplt.fill_between(low, high, color = light_gray)

    # init dataframe plot entities
    entities = pd.DataFrame(
        index = data.index,
        dtype = float,
        columns = [
            'long_entry',
            'long_trade',
            'short_entry',
            'short_trade'
            'profit_exit',
            'loss_exit' ])

    for trade in tqdm(
        iterable = engine.trades,
        colour = green,
        bar_format='        Plot:           {percentage:3.0f}%|{bar:100}{r_bar}'):

        # entry
        entry_idx = trade.entry_order.idx
        entry_price = trade.entry_order.price
        entry_bar = trade.entry_order.bar_index

        if trade.is_long: entities.loc[entry_idx, 'long_entry'] = entry_price
        else: entities.loc[entry_idx, 'short_entry'] = entry_price

        # exit
        exit_idx = trade.exit_order.idx
        exit_price = trade.exit_order.price
        exit_bar = trade.exit_order.bar_index
        profit = trade.profit

        if profit > 0: entities.loc[exit_idx, 'profit_exit'] = exit_price
        else: entities.loc[exit_idx, 'loss_exit'] = exit_price

        # linear interpolate between entry and exit
        timestamps = pd.date_range(
            start = entry_idx,
            end = exit_idx,
            freq = '1min')

        # build trade line
        slope = (exit_price - entry_price) / (exit_bar - entry_bar)
        trade_bar = 0
        for timestamp in timestamps:

            # prevent gaps in plot
            if timestamp not in data.index: continue

            # y = mx + b
            price = slope * trade_bar + entry_price
            if trade.is_long: entities.loc[timestamp, 'long_trade'] = price
            else: entities.loc[timestamp, 'short_trade'] = price

            trade_bar += 1

    # entries
    fplt.plot(entities['long_entry'], style = 'o', color = blue, ax = ax)
    fplt.plot(entities['short_entry'], style = 'o', color = aqua, ax = ax)

    # exits
    fplt.plot(entities['profit_exit'], style = 'o', color = green, ax = ax)
    fplt.plot(entities['loss_exit'], style = 'o', color = red, ax = ax)

    # trades
    fplt.plot(entities['long_trade'], color = blue, ax = ax)
    fplt.plot(entities['short_trade'], color = aqua, ax = ax)

    # fplt.show()

def plot_strategy(engine):

    # maximize window
    fplt.winx = 3840
    fplt.winy = 0
    fplt.winw = 3840
    fplt.winh = 2160

    # colors
    white = 'white'
    light_gray = '#262626'
    dark_gray = '#1a1a1a'
    dark_black = '#141414'
    dark_blue = '#00165e'
    dark_aqua = '#00585e'
    gray = '#383838'

    fplt.background = dark_black
    fplt.candle_bull_color = light_gray
    fplt.candle_bull_body_color = light_gray
    fplt.candle_bear_color = dark_gray
    fplt.candle_bear_body_color = dark_gray
    fplt.cross_hair_color = white

    # init finplot
    ax = fplt.create_plot(title='Strategy')

    # axis
    axis_pen = fplt._makepen(color='grey')
    ax.axes['right']['item'].setPen(axis_pen)
    ax.axes['right']['item'].setTextPen(axis_pen)
    ax.axes['right']['item'].setTickPen(None)
    ax.axes['bottom']['item'].setPen(axis_pen)
    ax.axes['bottom']['item'].setTextPen(axis_pen)
    ax.axes['bottom']['item'].setTickPen(None)

    # crosshair
    ax.crosshair.vline.setPen(axis_pen)
    ax.crosshair.hline.setPen(axis_pen)

    # candlestick ohlc
    data = engine.data
    fplt.candlestick_ochl(data[['Open', 'Close', 'High', 'Low']], ax=ax, draw_body=False, draw_shadow=False)

    # cloud
    low = fplt.plot(data.Low, color=dark_black, width=0, ax=ax)
    high = fplt.plot(data.High, color=dark_black, width=0, ax=ax)
    fplt.fill_between(low, high, color = light_gray)

    markersize = 2
    linewidth = 7

    # build enabled long, short, and disabled
    fast = engine.strategy.fast
    fastSlope = engine.strategy.fastSlope
    fastAngle = engine.strategy.fastAngle
    slow = engine.strategy.slow
    slowSlope = engine.strategy.slowSlope
    slowAngle = engine.strategy.slowAngle

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

        if is_slow_long_enabled : slow_df.loc[idx, 'long_enabled'] = slow[idx]
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
    # fplt.plot(slow_df['long_enabled'], color=dark_blue, width=2, ax=ax)
    # fplt.plot(slow_df['short_enabled'], color=dark_aqua, width=2, ax=ax)
    # fplt.plot(slow_df['disabled'], color=gray, width=2, ax=ax)

    # overlay fast
    fplt.plot(fast_df['long_enabled'], color=gray, width=2, ax=ax)
    fplt.plot(fast_df['short_enabled'], color=gray, width=2, ax=ax)
    fplt.plot(fast_df['disabled'], color=gray, width=2, ax=ax)

    fplt.show()