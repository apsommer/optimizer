from time import strftime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates

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

    # pos_df.index = pos_df.index.strftime('%Y-%m-%d %H:%M:%S')

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

    init_figure(2)

    # plot underlying
    close = engine.data.Close
    plt.plot(close, color = '#3C3C3C')

    for trade in engine.trades:

        sentiment = trade.entry_order.sentiment
        entry_idx = trade.entry_order.idx
        entry_price = trade.entry_order.price

        color = 'blue' # long
        if sentiment == 'short': color = 'aqua'

        # last trade open
        if trade.is_open:
            exit_idx = engine.data.index[-1]
            exit_price = engine.data.Close[exit_idx]
            lineColor = 'white'
        else:
            exit_idx = trade.exit_order.idx
            exit_price = trade.exit_order.price
            lineColor = color

        trade_df = pd.DataFrame(
            index = [entry_idx, exit_idx],
            data = [entry_price, exit_price])

        plt.plot(trade_df, lineColor)
        plt.plot(entry_idx, entry_price, color=color, marker='o', markersize=5)
        plt.plot(exit_idx, exit_price, color=lineColor, marker='o', markersize=10)

    # show
    plt.tight_layout()
    plt.show(block=True)

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