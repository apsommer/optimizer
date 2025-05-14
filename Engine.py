import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from model.Trade import Trade

class Engine:

    def __init__(self, initial_cash = 1_000):
        self.data = None
        self.strategy = None
        self.current_idx = None
        self.trades = []
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.cash_series = { }

    def add_data(self, data: pd.DataFrame):
        self.data = data

    def add_strategy(self, strategy):
        self.strategy = strategy

    def run(self):

        # init strategy
        self.strategy.data = self.data
        self.strategy.cash = self.cash

        # loop timestamps
        for idx in tqdm(self.data.index, colour='BLUE'):

            # set index todo refactor to single index, remove replication
            self.current_idx = idx
            self.strategy.current_idx = self.current_idx

            if len(self.strategy.orders) == 0: continue

            # fill order from previous period
            last_order = self.strategy.orders[-1]
            if last_order.idx == self.current_idx:
                self._fill_order()

            # execute strat
            self.strategy.on_bar()

            # track cash and asset holdings
            self.cash_series[idx] = self.cash

        return self._get_stats()

    def _fill_order(self):

        entry_order = self.strategy.orders[-2]
        exit_order = self.strategy.orders[-1]

        if entry_order.side == 'buy' and exit_order.side == 'sell' and self.strategy.position_size == 0:
            profit = exit_order.price - entry_order.price
        elif entry_order.side == 'sell' and exit_order.side == 'buy' and self.strategy.position_size == 0:
            profit = entry_order.price - exit_order.price

        trade = Trade(
            ticker = exit_order.ticker,
            side = exit_order.side,
            size = exit_order.size,
            idx = self.current_idx,
            type = exit_order.type,
            profit = profit)

        self.trades.append(trade)
        self.cash = sum([trade.profit for trade in self.trades])

    def _get_stats(self):

        metrics = { }

        metrics['total_return'] = (self.cash / self.initial_cash) * 100
        metrics['trades'] = len(self.trades)

        # reference buy and hold
        portfolio_buy_hold = (self.initial_cash / self.data.loc[self.data.index[0]]['Open']) * self.data.Close

        portfolio = pd.DataFrame({
            'stock': self.cash_series, # todo temp for development
            'cash': self.cash_series})

        # assets under management
        portfolio['total_aum'] = portfolio['stock'] + portfolio['cash']

        # average exposure: percent of stock relative to total aum
        metrics['exposure_pct'] = ((portfolio['stock'] / portfolio['total_aum']) * 100).mean()

        # annualized returns: ((1 + r_1) * (1 + r_2) * ... * (1 + r_n)) ^ (1/n) - 1
        # aum = portfolio['total_aum']
        # metrics['returns_annualized'] = (
        #         ((aum.iloc[-1] / aum.iloc[0])
        #          ** (1 / ((aum.index[-1] - aum.index[0]).days / 365)) - 1) * 100)

        ref = portfolio_buy_hold
        metrics['returns_annualized_buy_hold'] = (
                ((ref.iloc[-1] / ref.iloc[0])
                 ** (1 / ((ref.index[-1] - ref.index[0]).days / 365)) - 1) * 100)

        # annualized volatility: std_dev * sqrt(periods/year)
        self.trading_days = 252
        # metrics['volatility_ann'] = aum.pct_change().std() * np.sqrt(self.trading_days) * 100
        # metrics['volatility_ann_buy_hold'] = ref.pct_change().std() * np.sqrt(self.trading_days) * 100

        # sharpe ratio: (rate - risk_free_rate) / volatility
        self.risk_free_rate = 0
        # metrics['sharpe_ratio'] = (metrics['returns_annualized'] - self.risk_free_rate) / metrics['volatility_ann']
        # metrics['sharpe_ratio_buy_hold'] = (metrics['returns_annualized_buy_hold'] - self.risk_free_rate) / metrics[
        #     'volatility_ann_buy_hold']

        # max drawdown, percent
        metrics['max_drawdown'] = get_max_drawdown(portfolio.total_aum)
        metrics['max_drawdown_buy_hold'] = get_max_drawdown(portfolio_buy_hold)

        # capture portfolios for plotting
        self.portfolio = portfolio
        self.portfolio_buy_hold = portfolio_buy_hold

        return metrics

    def plot(self):
        plt.plot(self.portfolio['total_aum'], label='Strategy')
        plt.plot(self.portfolio_buy_hold, label='Buy & Hold')
        plt.grid(color='#dee0df', linewidth=0.1)
        plt.legend()
        plt.show()

    def print_trades(self):
        print("")
        for trade in self.trades:
            print(trade)
        print("")

def get_max_drawdown(close):
    roll_max = close.cummax()
    daily_drawdown = close / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin()
    return max_daily_drawdown.min() * 100

def print_stats(metrics):
    print("")
    print("Performance:")
    print("")
    for stat, value in metrics.items():
        print("{}: {}".format(stat, round(value, 5)))
    print("")
