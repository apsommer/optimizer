import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib
import matplotlib.pyplot as plt
from model.Trade import Trade

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
        self.initial_cash = margin_requirement * self.first_bar_close
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

        stats['Config:'] = ''

        stats['start_date'] = str(self.data.index[0])
        stats['end_date'] = str(self.data.index[-1])
        days = (self.data.index[-1] - self.data.index[0]).days
        stats['days'] = days
        stats['ticker'] = self.strategy.ticker.symbol
        stats['size'] = self.strategy.size
        stats['initial_cash [$]'] = self.initial_cash

        stats['Strategy:'] = ''

        stats['trades'] = len(self.trades)
        stats['profit [$]'] = self.cash - self.initial_cash

        total_return = (abs(self.cash - self.initial_cash) / self.initial_cash ) * 100
        if self.initial_cash > self.cash:
            total_return = - total_return
        stats['total_return [%]'] = total_return

        cash_df = pd.DataFrame({'cash': self.cash_series})
        stats['annualized_return [%]'] = ((self.cash / self.initial_cash) ** (1 / (days / 365)) - 1) * 100
        stats['max_drawdown [%]'] = get_max_drawdown(cash_df['cash'])

        stats['Buy & Hold:'] = ''
        stats['trades_bh'] = 1

        buy_hold_df = self.initial_cash + self.strategy.ticker.tick_value * (self.data.Close - self.first_bar_close)

        profit_buy_hold = buy_hold_df.iloc[-1] - buy_hold_df.iloc[0]
        stats['profit_bh [$]'] =  profit_buy_hold

        total_return_buy_hold = (abs(profit_buy_hold) / buy_hold_df.iloc[0]) * 100
        if self.first_bar_close > self.last_bar_close:
            total_return_buy_hold = - total_return_buy_hold
        stats['total_return_bh [%]'] = total_return_buy_hold
        stats['annualized_return_bh [%]'] = ((buy_hold_df.iloc[-1] / buy_hold_df.iloc[0]) ** (1 / (days / 365)) - 1) * 100
        stats['max_drawdown_bh [%]'] = get_max_drawdown(buy_hold_df)

        # todo annualized volatility: std_dev * sqrt(periods/year)
        self.trading_days = 252
        # metrics['volatility_ann'] = aum.pct_change().std() * np.sqrt(self.trading_days) * 100
        # metrics['volatility_ann_buy_hold'] = ref.pct_change().std() * np.sqrt(self.trading_days) * 100

        # sharpe ratio: (rate - risk_free_rate) / volatility
        self.risk_free_rate = 0
        # metrics['sharpe_ratio'] = (metrics['returns_annualized'] - self.risk_free_rate) / metrics['volatility_ann']
        # metrics['sharpe_ratio_buy_hold'] = (metrics['returns_annualized_buy_hold'] - self.risk_free_rate) / metrics[
        #     'volatility_ann_buy_hold']

        # capture portfolios for plotting
        self.portfolio = cash_df
        self.portfolio_buy_hold = buy_hold_df

        return stats

    def plot(self):

        plt.get_current_fig_manager().full_screen_toggle()
        font = {'family': 'Ubuntu', 'size': 16}
        matplotlib.rc('font', **font)

        plt.plot(self.portfolio['cash'], label='strategy', color = 'blue')
        plt.plot(self.portfolio_buy_hold, label='b & h', color = 'green')

        xmin = min(self.data.index)
        xmax = max(self.data.index)
        xstep = 20
        x_ticks = pd.date_range(xmin, xmax, xstep)
        plt.xticks(x_ticks, rotation = 90)
        plt.xlim(xmin, xmax)

        abs_ymin = min(min(self.cash_series.values()), min(self.portfolio_buy_hold))
        abs_ymax = max(max(self.cash_series.values()), max(self.portfolio_buy_hold))
        ymin = round(1.10 * abs_ymin, -2)
        ymax = round(1.10 * abs_ymax, -2)
        ystep = round((ymax - ymin) / 20, -2)
        y_ticks = np.arange(ymin, ymax, ystep)
        plt.yticks(y_ticks)
        plt.ylim(ymin, ymax)

        plt.tick_params(tick1On = False)
        plt.tick_params(tick2On = False)

        plt.grid(color = '#f2f2f2', linewidth = 0.5)

        plt.legend()
        plt.tight_layout()
        plt.show()

    def print_trades(self):
        print("")
        for trade in self.trades:
            print(trade)
        print("")

def get_max_drawdown(prices):
    roll_max = prices.cummax()
    daily_drawdown = prices / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin()
    return max_daily_drawdown.min() * 100

def print_stats(stats):
    print()
    for stat, value in stats.items():
        if type(value) == np.float64 or type(value) == float:
            value = round(value, 1)
            if abs(value) > 10:
                value = round(value)
        if ":" in stat:
            print(stat)
            continue
        print("\t{}: {}".format(stat, value))
    print()
