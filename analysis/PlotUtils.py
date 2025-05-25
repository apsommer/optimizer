import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def init_figure(fig_id, data):

    # size
    plt.rcParams['figure.figsize'] = [20, 12]

    # font color
    color = 'white'
    font = {'family': 'Ubuntu', 'size': 14}
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

    xstep = 20
    ystep = 20

    # x-axis
    xmin = min(data.index)
    xmax = max(data.index)
    x_ticks = pd.date_range(xmin, xmax, xstep)
    plt.xticks(x_ticks, rotation=90)
    plt.xlim(xmin, xmax)

    # y-axis
    # ymin = round(min(data), -2)
    # ymax = round(max(data), -2)
    # ystep = round((ymax - ymin) / ystep, -2)
    # y_ticks = np.arange(ymin, ymax, ystep)
    # plt.yticks(y_ticks)
    # plt.ylim(ymin, ymax)

    # grid
    plt.tick_params(tick1On=False)
    plt.tick_params(tick2On=False)
    plt.grid(color='#1D193B', linewidth=0.5)

    return fig

def plot_equity(engine):

    # init figure
    cash_series = engine.cash_series
    init_figure(1, cash_series)

    # split cash balance into profit and loss
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

    # init figure
    close = engine.data.Close
    init_figure(2, close)

    # plot underlying
    plt.plot(close, color = '#3C3C3C')

    for trade in engine.trades:

        # skip last open trade, if needed
        if trade.exit_order is None: continue

        sentiment = trade.entry_order.sentiment
        entry_idx = trade.entry_order.idx
        exit_idx = trade.exit_order.idx
        entry_price = trade.entry_order.price
        exit_price = trade.exit_order.price

        trade_df = pd.DataFrame(
            index = [entry_idx, exit_idx],
            data = [entry_price, exit_price])

        color = 'blue' # long
        if sentiment == 'short': color = 'aqua'

        plt.plot(trade_df, color)
        plt.plot(entry_idx, entry_price, color=color, marker='o', markersize=5)
        plt.plot(exit_idx, exit_price, color=color, marker='o', markersize=10)

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