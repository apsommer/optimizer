from tqdm import tqdm
from model.Trade import Trade
from EngineUtils import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as matplotlib

class Engine:

    def __init__(self):
        self.data = None
        self.strategy = None
        self.current_idx = -1
        self.initial_cash = 0
        self.cash = self.initial_cash
        self.trades = []
        self.cash_series = { } # todo refactor to series
        self.stats = { }

    @property
    def first_bar_close(self):
        return self.data.iloc[0]['Close']

    @property
    def last_bar_close(self):
        return self.data.iloc[-1]['Close']

    def run(self):

        margin_requirement = self.strategy.ticker.margin_requirement
        size = self.strategy.size

        # init
        self.initial_cash = 10e3 # margin_requirement * self.first_bar_close
        self.cash = self.initial_cash
        self.strategy.data = self.data

        # loop timestamps
        for idx in tqdm(self.data.index, colour='BLUE'):

            # set index todo refactor to single index, remove replication
            self.current_idx = idx
            self.strategy.current_idx = self.current_idx

            # execute strat
            self.strategy.on_bar()

            # fill order, if needed
            orders = self.strategy.orders
            if len(orders) > 0 and orders[-1].idx == self.current_idx:
                self._fill_order()

            # track cash and asset holdings
            self.cash_series[idx] = self.cash

        return self._get_stats()

    def _fill_order(self):

        last_order = self.strategy.orders[-1]
        profit = 0

        if (last_order.sentiment == 'long'
                or last_order.sentiment == 'short'):

            trade = Trade(
                side = last_order.sentiment, # long, short
                size = last_order.size,
                entry_order = last_order,
                exit_order = None)

            self.trades.append(trade)

        elif last_order.sentiment == 'flat':

            last_trade = self.trades[-1]
            last_trade.exit_order = last_order
            profit = last_trade.profit

        self.cash += profit

    def _get_stats(self):

        stats = self.stats
        trading_days = 252
        risk_free_rate = 0

        # config
        stats['Config:'] = ''
        stats['start_date'] = str(self.data.index[0])
        stats['end_date'] = str(self.data.index[-1])
        days = (self.data.index[-1] - self.data.index[0]).days
        stats['days'] = days
        stats['ticker'] = self.strategy.ticker.symbol
        stats['size'] = self.strategy.size
        stats['initial_cash [$]'] = self.initial_cash

        # strategy
        cash_df = pd.DataFrame({'cash': self.cash_series})
        trades = len(self.trades)
        profit = self.cash - self.initial_cash
        max_drawdown = -get_max_drawdown(cash_df['cash'])
        total_return = (abs(self.cash - self.initial_cash) / self.initial_cash ) * 100
        if self.initial_cash > self.cash:
            total_return = - total_return
        annualized_return = ((self.cash / self.initial_cash) ** (1 / (days / 365)) - 1) * 100
        volatility = cash_df['cash'].pct_change().std() * np.sqrt(trading_days) * 100

        stats['Strategy:'] = ''
        stats['trades'] = trades
        stats['pf'] = get_profit_factor(self.trades)
        stats['profit [$]'] = profit
        stats['total_return [%]'] = total_return
        stats['annualized_return [%]'] = annualized_return
        stats['max_drawdown [$]'] = max_drawdown
        stats['drawdown/profit [%]'] = (max_drawdown / profit) * 100
        stats['annualized_volatility [%]'] = volatility # todo check
        stats['sharpe'] = (annualized_return - risk_free_rate) / volatility # todo check
        stats['expectancy'] = 'todo'
        stats['trades/day'] = trades / days

        # reference simple "buy and hold"
        buy_hold_df = self.initial_cash + self.strategy.ticker.tick_value * (self.data.Close - self.first_bar_close)
        profit_buy_hold = buy_hold_df.iloc[-1] - buy_hold_df.iloc[0]
        total_return_buy_hold = (abs(profit_buy_hold) / buy_hold_df.iloc[0]) * 100
        if self.first_bar_close > self.last_bar_close:
            total_return_buy_hold = - total_return_buy_hold
        annualized_return_buy_hold = ((buy_hold_df.iloc[-1] / buy_hold_df.iloc[0]) ** (1 / (days / 365)) - 1) * 100
        volatility_buy_hold = buy_hold_df.pct_change().std() * np.sqrt(trading_days) * 100

        stats['Buy & Hold:'] = ''
        stats['profit_bh [$]'] = profit_buy_hold
        stats['total_return_bh [%]'] = total_return_buy_hold
        stats['annualized_return_bh [%]'] = annualized_return_buy_hold
        stats['max_drawdown_bh [%]'] = get_max_drawdown(buy_hold_df)
        stats['volatility_ann_bh [%]'] = volatility_buy_hold # todo check
        stats['sharpe_ratio_bh'] = (annualized_return_buy_hold - risk_free_rate) / volatility_buy_hold # todo check

        self.portfolio = cash_df
        self.portfolio_buy_hold = buy_hold_df

        return stats

    def plot_strategy(self):

        # config plot
        fig_id = 1
        data = self.portfolio['cash']

        # todo duplicate
        font = {'family': 'Ubuntu', 'size': 14}
        matplotlib.rc('font', **font)

        color = 'white'
        matplotlib.rcParams['text.color'] = color
        matplotlib.rcParams['axes.labelcolor'] = color
        matplotlib.rcParams['xtick.color'] = color
        matplotlib.rcParams['ytick.color'] = color

        fig = plt.figure(fig_id)
        ax = plt.gca()

        fig.patch.set_facecolor('#0D0B1A')  # outside grid
        ax.patch.set_facecolor('#131026')  # inside grid

        # x-axis
        xmin = min(data.index)
        xmax = max(data.index)
        xstep = 20
        x_ticks = pd.date_range(xmin, xmax, xstep)
        plt.xticks(x_ticks, rotation=90)
        plt.xlim(xmin, xmax)

        # y-axis
        data_min = min(data)
        data_max = max(data)
        buy_hold_min = min(self.portfolio_buy_hold)
        buy_hold_max = max(self.portfolio_buy_hold)
        ymin = round(0.95 * min(data_min, buy_hold_min), -2)
        ymax = round(1.05 * max(data_max, buy_hold_max), -2)
        ystep = round((ymax - ymin) / 20, -2)
        y_ticks = np.arange(ymin, ymax, ystep)
        plt.yticks(y_ticks)
        plt.ylim(ymin, ymax)

        plt.tick_params(tick1On=False)
        plt.tick_params(tick2On=False)
        plt.grid(color='#1D193B', linewidth=0.5)

        # add series
        plt.plot(data, color = 'green', label='strategy')
        plt.plot(self.portfolio_buy_hold, color = '#3C3C3C', label='buy/hold')

        # show
        plt.legend(
            facecolor='#0D0B1A',
            frameon=False)
        plt.tight_layout()
        plt.show(block=False)

    def plot_trades(self,):

        # config plot
        fig_id = 2
        data = self.data.Close

        # todo duplicate
        font = {'family': 'Ubuntu', 'size': 14}
        matplotlib.rc('font', **font)

        color = 'white'
        matplotlib.rcParams['text.color'] = color
        matplotlib.rcParams['axes.labelcolor'] = color
        matplotlib.rcParams['xtick.color'] = color
        matplotlib.rcParams['ytick.color'] = color

        fig = plt.figure(fig_id)
        ax = plt.gca()

        fig.patch.set_facecolor('#0D0B1A')  # outside grid
        ax.patch.set_facecolor('#131026')  # inside grid

        # x-axis
        xmin = min(data.index)
        xmax = max(data.index)
        xstep = 20
        x_ticks = pd.date_range(xmin, xmax, xstep)
        plt.xticks(x_ticks, rotation=90)
        plt.xlim(xmin, xmax)

        # y-axis
        ymin = round(0.90 * min(data), -2)
        ymax = round(1.10 * max(data), -2)
        ystep = round((ymax - ymin) / 20, -2)
        y_ticks = np.arange(ymin, ymax, ystep)
        plt.yticks(y_ticks)
        plt.ylim(ymin, ymax)

        plt.tick_params(tick1On=False)
        plt.tick_params(tick2On=False)
        plt.grid(color='#1D193B', linewidth=0.5)

        # add series
        plt.plot(data, color = '#3C3C3C')

        for trade in self.trades:

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

            match sentiment:
                case 'long': color = 'blue'
                case 'short': color = 'aqua'

            plt.plot(trade_df, color)
            plt.plot(entry_idx, entry_price, color=color, marker='o', markersize=5)
            plt.plot(exit_idx, exit_price, color=color, marker='o', markersize=10)

        # show
        plt.tight_layout()
        plt.show(block=True)

    def print_trades(self):
        print("")
        for trade in self.trades:
            print(trade)
        print("")

def print_stats(stats):
    print()
    for stat, value in stats.items():
        if type(value) == np.float64 or type(value) == float:
            value = round(value, 1)
            if abs(value) > 0 and abs(value) < 10:
                value = round(value, 2)
            if abs(value) > 10 and abs(value) < 100:
                    value = round(value, 1)
            if abs(value) > 100:
                value = round(value)
        if ":" in stat:
            print(stat)
            continue
        print("\t{}: {}".format(stat, value))
    print()
