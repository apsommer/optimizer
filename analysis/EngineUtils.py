import numpy as np
import matplotlib as matplotlib
import matplotlib.pyplot as plt
import pandas as pd

def get_max_drawdown(prices):
    roll_max = prices.cummax()
    daily_drawdown = prices / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin()
    return max_daily_drawdown.min() * 100

def get_profit_factor(trades):
    wins = [trade.profit for trade in trades if trade.profit > 0]
    losses = [trade.profit for trade in trades if trade.profit < 0]
    total_wins = sum(wins)
    total_losses = -sum(losses)
    if total_losses > total_wins: return np.nan
    return total_wins / total_losses

def plot(fig_id, data, label, data_color):

    # config plot
    font = {'family': 'Ubuntu', 'size': 14}
    matplotlib.rc('font', **font)

    color = 'white'
    matplotlib.rcParams['text.color'] = color
    matplotlib.rcParams['axes.labelcolor'] = color
    matplotlib.rcParams['xtick.color'] = color
    matplotlib.rcParams['ytick.color'] = color

    plt.tick_params(tick1On = False)
    plt.tick_params(tick2On = False)
    plt.grid(color = '#1D193B', linewidth = 0.5)

    fig = plt.figure(fig_id)
    ax = plt.gca()

    fig.patch.set_facecolor('#0D0B1A') # outside grid
    ax.patch.set_facecolor('#131026') # inside grid

    # x-axis
    xmin = min(data.index)
    xmax = max(data.index)
    xstep = 20
    x_ticks = pd.date_range(xmin, xmax, xstep)
    plt.xticks(x_ticks, rotation = 90)
    plt.xlim(xmin, xmax)

    # y-axis
    # abs_ymin = min(min(self.cash_series.values()), min(self.portfolio_buy_hold))
    # abs_ymax = max(max(self.cash_series.values()), max(self.portfolio_buy_hold))
    # ymin = round(0.90 * abs_ymin, -2)
    # ymax = round(1.10 * abs_ymax, -2)
    ymin = round(0.90 * min(data), -2)
    ymax = round(1.10 * max(data), -2)
    ystep = round((ymax - ymin) / 20, -2)
    y_ticks = np.arange(ymin, ymax, ystep)
    plt.yticks(y_ticks)
    plt.ylim(ymin, ymax)

    # add series
    # plt.get_current_fig_manager().full_screen_toggle()
    # plt.plot(self.portfolio['cash'], label='strategy', color = 'green')
    # plt.plot(self.portfolio_buy_hold, label='buy hold', color = 'white')
    plt.plot(data, label=label, color=data_color)

    # show
    plt.legend(facecolor = '#0D0B1A')
    plt.tight_layout()
    plt.show(block=False)
