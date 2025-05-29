import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import finplot as fplt

def init_figure(fig_id):

    # size
    plt.rcParams['figure.figsize'] = [24, 12]

    # font color
    color = 'white'
    font = {'family': 'Ubuntu', 'size': 18}
    matplotlib.rc('font', **font)
    matplotlib.rcParams['text.color'] = color
    matplotlib.rcParams['axes.labelcolor'] = color
    matplotlib.rcParams['xtick.color'] = color
    matplotlib.rcParams['ytick.color'] = color

    fig = plt.figure(fig_id)
    ax = plt.gca()

    # background color
    fig.patch.set_facecolor('#0D0B1A')  # outside grid
    ax.patch.set_facecolor('#131026')  # inside grid

    # x-axis, strftime() does not support single digit days, months ... everything "zero-padded"
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter('%d/%b  %H:%M'))

    plt.xticks(rotation=90)

    # grid
    plt.tick_params(tick1On=False)
    plt.tick_params(tick2On=False)
    plt.grid(color='#1D193B', linewidth=0.5)

    return fig

def plot_equity(engine):

    init_figure(1)

    # split cash balance into profit and loss
    cash_series = engine.cash_series
    pos, neg = [], []

    for balance in cash_series:

        over = balance >= engine.initial_cash
        under = balance < engine.initial_cash
        cross_over = over and len(pos) > 0 and np.isnan(pos[-1])
        cross_under = under and len(pos) > 0 and np.isnan(neg[-1])

        if over:
            pos.append(balance)
            neg.append(np.nan)
        elif under:
            pos.append(np.nan)
            neg.append(balance)

        # keep balance line continuous
        if cross_over: pos[-2] = neg[-2]
        if cross_under: neg[-2] = pos[-2]

    pos_df = pd.DataFrame({'pos': pos})
    neg_df = pd.DataFrame({'neg': neg})
    pos_df.index = cash_series.index
    neg_df.index = cash_series.index

    # add series
    plt.plot(pos_df, color = 'green')
    plt.plot(neg_df, color = 'red')

    # initial cash
    initial_cash_df = pd.DataFrame(
        data = { 'initial_cash': engine.initial_cash},
        index = cash_series.index)
    plt.plot(initial_cash_df, color = 'black')

    # buy and hold reference
    buy_hold = (engine.data.Close - engine.data.Open.iloc[0]) * engine.strategy.ticker.tick_value + engine.initial_cash
    plt.plot(buy_hold,  color = '#3C3C3C')

    plt.autoscale(axis='y')

    # show
    plt.tight_layout()
    plt.show(block=False)

def plot_trades(engine):

    # maximize window
    fplt.winx = 0
    fplt.winy = 0
    fplt.winw = 3840
    fplt.winh = 2160

    light_gray = '#505050'
    dark_gray = '#363636'
    white = '#ffffff'
    dark_black = '#141414'

    fplt.background = dark_black
    # fplt.odd_plot_background = light_black

    fplt.candle_bull_color = light_gray
    fplt.candle_bull_body_color = light_gray
    fplt.candle_bear_color = dark_gray
    fplt.candle_bear_body_color = dark_gray

    fplt.poc_color = white
    fplt.band_color = white
    fplt.cross_hair_color = white
    fplt.draw_line_color = white
    fplt.draw_done_color = white

    marksize = 2
    linewidth = 7

    # candlestick ohlc
    data = engine.data
    ax = fplt.create_plot()
    fplt.candlestick_ochl(data, ax=ax)

    for trade in engine.trades:

        # init container of nan
        trade_df = pd.DataFrame(
            data=np.full([len(data), 3], np.nan),
            columns=['entry', 'exit', 'trade'],
            index=data.index)

        # entry
        entry_idx = trade.entry_order.idx
        entry_price = trade.entry_order.price
        entry_bar = trade.entry_order.bar_index

        if trade.is_long: entry_color = 'blue' # long
        else: entry_color = 'aqua' # short

        # closed trade
        if trade.is_closed:

            profit = trade.profit
            if profit > 0: exit_color = 'green' # profit
            else: exit_color = 'red' # loss

            exit_idx = trade.exit_order.idx
            exit_price = trade.exit_order.price
            exit_bar = trade.exit_order.bar_index

        # last trade is open
        else:
            exit_idx = engine.data.index[-1]
            exit_price = engine.data.Close[exit_idx]
            exit_bar = len(engine.data.Close) - 1
            exit_color = 'white'

        # linear interpolate between entry and exit
        timestamps = pd.date_range(entry_idx, exit_idx, freq='1min')
        slope = (exit_price - entry_price) / (exit_bar - entry_bar)
        trade_bar = 0
        for timestamp in timestamps:
            if timestamp not in data.index: continue # prevent gaps in plot
            trade_df.loc[timestamp, 'trade'] = slope * trade_bar + entry_price # y = mx + b
            trade_bar += 1

        # overlay entry
        trade_df.loc[entry_idx, 'entry'] = entry_price
        fplt.plot(
            trade_df['entry'],
            style='o',
            color=entry_color,
            width=marksize,
            ax=ax)

        # overlay exit
        trade_df.loc[exit_idx, 'exit'] = exit_price
        fplt.plot(
            trade_df['exit'],
            style='o',
            color=exit_color,
            width=marksize,
            ax=ax)

        # overlay trade
        fplt.plot(
            trade_df['trade'],
            color=entry_color,
            width=linewidth,
            ax=ax)

    fplt.show()

def print_metrics(engine):

    for metric in engine.metrics:

        title = metric.title
        value = metric.value
        formatter = metric.formatter
        unit = metric.unit

        # header
        if value is None:
            print('\n' + title)
            continue

        if unit is None and formatter is None:
            print("\t{}: {}".format(title, value))
            continue

        rounded_value = format(value, '.0f')
        if formatter is not None: rounded_value = format(value, formatter)

        if unit is None:
            print("\t{}: {}".format(title, rounded_value))
            continue

        print("\t{}: {} [{}]".format(title, rounded_value, unit))