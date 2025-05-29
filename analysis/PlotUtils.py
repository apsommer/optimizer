import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import finplot as fplt
from sympy.strategies.core import switch


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

    fplt.background = '#0D0B1A'
    fplt.odd_plot_background = '#131026'

    candleColor = '#9c9c9c'
    fplt.candle_bull_color = candleColor
    fplt.candle_bear_color = candleColor
    fplt.candle_bull_body_color = candleColor
    fplt.candle_bear_body_color = candleColor

    # candlestick ohlc
    data = engine.data
    ax = fplt.create_plot()
    fplt.candlestick_ochl(
        data,
        ax = ax)

    for trade in engine.trades:

        # init container of nan
        trade_df = pd.DataFrame(
            data=np.full([len(data), 2], np.nan),
            columns=['trade', 'color'],
            index=data.index)

        # entry
        entry_idx = trade.entry_order.idx
        entry_price = trade.entry_order.price
        entry_bar = trade.entry_order.bar_index

        # sentiment
        # 1 orange, 2 green, 3 red, 4 purple, 5 brown, 6 pink, 7 gray, 8 yellow, 9 aqua, 10 blue
        sentiment = trade.entry_order.sentiment
        match sentiment:
            case "long": entryColor = 10
            case "short": entryColor = 4
            case _: entryColor = 1

        # closed trade
        if trade.is_closed:

            profit = trade.profit
            if profit > 0: exitColor = 'green'  # profit
            else: exitColor = 'red'  # loss

            exit_idx = trade.exit_order.idx
            exit_price = trade.exit_order.price
            exit_bar = trade.exit_order.bar_index

        # last trade is open
        else:
            exit_idx = engine.data.index[-1]
            exit_price = engine.data.Close[exit_idx]
            exit_bar = len(engine.data.Close) - 1
            exitColor = 'white'

        # linear interpolate between entry and exit
        timestamps = pd.date_range(entry_idx, exit_idx, freq='1min')
        slope = (exit_price - entry_price) / (exit_bar - entry_bar)
        trade_bar = 0
        for timestamp in timestamps:
            if timestamp not in data.index: continue # prevent gaps in plot
            trade_df.loc[timestamp, 'trade'] = slope * trade_bar + entry_price # y = mx + b
            trade_df.loc[timestamp, 'color'] = entryColor
            trade_bar += 1

        # overlay trade
        fplt.plot(
            trade_df['trade'],
            color=entryColor,
            width=10,
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