import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as matplotlib

def get_max_drawdown(prices):

    initial_price = prices.iloc[0]
    roll_max = prices.cummax() # series, rolling maximum
    daily_drawdown = prices / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin() # series, rolling minimum
    return max_daily_drawdown.min() * initial_price

def get_profit_factor(trades):

    wins = [trade.profit for trade in trades if trade.profit > 0]
    losses = [trade.profit for trade in trades if trade.profit < 0]
    total_wins = sum(wins)
    total_losses = -sum(losses)
    if total_losses > total_wins: return np.nan
    return total_wins / total_losses

def init_figure(fig_id, data):

    plt.rcParams['figure.figsize'] = [20, 12]

    color = 'white'
    font = {'family': 'Ubuntu', 'size': 14}
    matplotlib.rc('font', **font)
    matplotlib.rcParams['text.color'] = color
    matplotlib.rcParams['axes.labelcolor'] = color
    matplotlib.rcParams['xtick.color'] = color
    matplotlib.rcParams['ytick.color'] = color

    fig = plt.figure(fig_id)
    ax = plt.gca()

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
    ymin = round(0.95 * min(data), -2)
    ymax = round(1.05 * max(data), -2)
    ystep = round((ymax - ymin) / ystep, -2)
    y_ticks = np.arange(ymin, ymax, ystep)
    plt.yticks(y_ticks)
    plt.ylim(ymin, ymax)

    plt.tick_params(tick1On=False)
    plt.tick_params(tick2On=False)
    plt.grid(color='#1D193B', linewidth=0.5)

    return fig