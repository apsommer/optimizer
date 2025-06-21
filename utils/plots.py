import numpy as np
import pandas as pd
import finplot as fplt

# todo
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