import numpy as np
import pandas as pd
import finplot as fplt
from tqdm import tqdm

# todo extract common plot init

def plot_equity(engine):

    # maximize window (left)
    fplt.winx = 0
    fplt.winy = 0
    fplt.winw = 3840
    fplt.winh = 2160

    # colors
    white = 'white'
    light_gray = '#9e9e9e'
    dark_gray = '#1a1a1a'
    dark_black = '#141414'

    fplt.background = dark_black
    fplt.candle_bull_color = light_gray
    fplt.candle_bull_body_color = light_gray
    fplt.candle_bear_color = dark_gray
    fplt.candle_bear_body_color = dark_gray
    fplt.cross_hair_color = white

    # init finplot
    ax = fplt.create_plot(title='Equity')

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

    # plot initial cash line first
    cash_series = engine.cash_series
    initial_cash_df = pd.DataFrame(
        data = { 'initial_cash': engine.initial_cash},
        index = cash_series.index)
    fplt.plot(
        initial_cash_df,
        color = 'black',
        ax = ax)

    # reference simple buy and hold
    size = engine.strategy.size
    point_value = engine.strategy.ticker.point_value
    delta_df = engine.data.Close - engine.data.Close.iloc[0]
    initial_cash = engine.initial_cash
    buy_hold = size * point_value * delta_df + initial_cash

    # plot buy and hold
    fplt.plot(
        buy_hold,
        color=light_gray,
        width=2,
        ax=ax)

    # split balance into positive and negative
    pos, neg = [], []
    for balance in cash_series:

        over = balance >= engine.initial_cash
        under = balance < engine.initial_cash

        if over:
            pos.append(balance)
            neg.append(np.nan)
            if len(pos) > 1 and np.isnan(pos[-2]):
                pos[-2] = neg[-2]
        elif under:
            pos.append(np.nan)
            neg.append(balance)
            if len(neg) > 1 and np.isnan(neg[-2]):
                neg[-2] = pos[-2]

    pos_df = pd.DataFrame({'pos': pos})
    neg_df = pd.DataFrame({'neg': neg})
    pos_df.index = cash_series.index
    neg_df.index = cash_series.index

    # plot positive and negative
    fplt.plot(
        pos_df,
        color = 'green',
        ax=ax)
    fplt.plot(
        neg_df,
        color = 'red',
        ax=ax)

    fplt.show()

def plot_trades(engine):

    # maximize window (right)
    fplt.winx = 3840
    fplt.winy = 0
    fplt.winw = 3840
    fplt.winh = 2160

    # colors
    white = 'white'
    light_gray = '#262626'
    gray = '#1a1a1a'
    black = '#141414'
    blue = '#4287f5'
    aqua = '#42f5f5'
    green = '#42f578'
    red = '#f55a42'

    fplt.background = black
    fplt.candle_bull_color = light_gray
    fplt.candle_bull_body_color = light_gray
    fplt.candle_bear_color = gray
    fplt.candle_bear_body_color = gray
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
    fplt.candlestick_ochl(
        data[['Open', 'Close', 'High', 'Low']],
        ax = ax) #, draw_body=False, draw_shadow=False)

    # cloud
    # low = fplt.plot(data.Low, color=black, width=0, ax=ax)
    # high = fplt.plot(data.High, color=black, width=0, ax=ax)
    # fplt.fill_between(low, high, color = light_gray)

    markersize = 1
    linewidth = 1

    # init dataframe plot entites
    columns = ['entry', 'exit', 'trade', 'entry_color', 'exit_color', 'trade_color']
    entities = pd.DataFrame(
        index = data.index,
        columns = columns)
    entities[['entry', 'exit', 'trade']] = (
        entities[['entry', 'exit', 'trade']].astype(float))
    entities[['entry_color', 'exit_color', 'trade_color']] = (
        entities[['entry_color', 'exit_color', 'trade_color']].astype(str))

    for trade in tqdm(
        iterable = engine.trades,
        colour = 'GREEN',
        bar_format = '       {percentage:3.0f}%|{bar:100}{r_bar}'):

        # entry
        entry_idx = trade.entry_order.idx
        entry_price = trade.entry_order.price
        entry_bar = trade.entry_order.bar_index

        entities.loc[entry_idx, 'entry'] = entry_price
        if trade.is_long: entities.loc[entry_idx, 'entry_color'] = blue
        else: entities.loc[entry_idx, 'entry_color'] = aqua

        # exit
        exit_idx = trade.exit_order.idx
        exit_price = trade.exit_order.price
        exit_bar = trade.exit_order.bar_index
        profit = trade.profit

        entities.loc[exit_idx, 'exit'] = exit_price
        if profit > 0: entities.loc[exit_idx, 'exit_color'] = green
        else: entities.loc[exit_idx, 'exit_color'] = red

        # if trade.is_short and profit > 0:
        #     print(f'exit_idx: {exit_idx}, side: {trade.side}, profit: {profit}, exit_color: {exit_color}')

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
            entities.loc[timestamp, 'trade'] = slope * trade_bar + entry_price
            trade_bar += 1

    for color in entities['entry_color']:
        if color == blue: print('blue')
        if color == aqua: print('aqua')

    # overlay entries
    fplt.plot(
        entities['entry'],
        style = 'o',
        color = entities['entry_color'].values,
        width = markersize,
        ax = ax)

    # # overlay exits
    # fplt.plot(
    #     entities['exit'],
    #     style = 'o',
    #     color = entities['exit_color'].items,
    #     width = markersize,
    #     ax = ax)
    #
    # # overlay trades
    # fplt.plot(
    #     entities['trade'],
    #     color = entities['trade_color'].items,
    #     width = linewidth,
    #     ax = ax)

    fplt.show()

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