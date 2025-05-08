import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from Trade import Trade

class Engine:

    def __init__(self, initial_cash = 100_000):
        self.data = None
        self.strategy = None
        self.current_idx = None
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.cash_series = { }
        self.stock_series = { }

    def add_data(self, data: pd.DataFrame):
        self.data = data

    def add_strategy(self, strategy):
        self.strategy = strategy

    def run(self):

        # pass data to strategy
        self.strategy.data = self.data
        self.strategy.cash = self.cash

        # tqdm library shows progress bar in terminal
        for idx in tqdm(self.data.index, colour = 'BLUE'):

            self.current_idx = idx
            self.strategy.current_idx = self.current_idx

            # fill orders from previous period
            self._fill_orders()
            self.strategy.on_bar()

            # track cash and stock holdings
            self.cash_series[idx] = self.cash
            self.stock_series[idx] = self.strategy.position_size * self.data.loc[self.current_idx]['Close']

        return self._get_stats()

    def _fill_orders(self):

        for order in self.strategy.orders:

            # todo set fill_price to open
            fill_price = self.data.loc[self.current_idx]['Open']
            can_fill = False

            # long: ensure enough cash exists to purchase qty
            if order.side == 'buy' and self.cash >= self.data.loc[self.current_idx]['Open'] * order.size:

                # limit buy filled if limit_price >= low
                if order.type == 'limit':

                    if order.limit_price >= self.data.loc[self.current_idx]['Low']:

                        fill_price = order.limit_price
                        can_fill = True
                    #     print(self.current_idx, 'Buy Filled. ', "limit", order.limit_price," / low", self.data.loc[self.current_idx]['Low'])
                    #
                    # else:
                    #     print(self.current_idx,'Buy NOT filled. ', "limit", order.limit_price," / low", self.data.loc[self.current_idx]['Low'])

                # market, always fills
                else:
                    can_fill = True

            # flatten (short): ensure position size is larger than qty sell
            elif order.side == 'sell' and self.strategy.position_size >= order.size:

                # limit sell filled if limit_price <= high
                if order.type == 'limit':

                    if order.limit_price <= self.data.loc[self.current_idx]['High']:

                        fill_price = order.limit_price
                        can_fill = True
                    #     print(self.current_idx, 'Sell filled. ', "limit", order.limit_price, " / high", self.data.loc[self.current_idx]['High'])
                    #
                    # else:
                    #     print(self.current_idx, 'Sell NOT filled. ', "limit", order.limit_price, " / high", self.data.loc[self.current_idx]['High'])

                # market, always fills
                else:
                    can_fill = True

            if can_fill:
                trade = Trade(
                    ticker = order.ticker,
                    side = order.side,
                    price = fill_price,
                    size = order.size,
                    type= order.type,
                    idx = self.current_idx)

                self.strategy.trades.append(trade)
                self.cash -= trade.price * trade.size
                self.strategy.cash = self.cash

        # clearing orders here assumes all limit orders are valid DAY, not GTC
        self.strategy.orders = []

    def _get_stats(self):

        metrics = { }

        # total percent return
        metrics['total_return'] = (
                ((self.data.loc[self.current_idx]['Close']
                * self.strategy.position_size + self.cash) / self.initial_cash - 1) * 100)

        # benchmark reference: buy and hold max allowed shares from start to end
        portfolio_buy_hold = (self.initial_cash / self.data.loc[self.data.index[0]]['Open']) * self.data.Close

        portfolio = pd.DataFrame({
            'stock': self.stock_series,
            'cash': self.cash_series})

        # assets under management
        portfolio['total_aum'] = portfolio['stock'] + portfolio['cash']

        # average exposure: percent of stock relative to total aum
        metrics['exposure_pct'] = ((portfolio['stock'] / portfolio['total_aum']) * 100).mean()

        # annualized returns: ((1 + r_1) * (1 + r_2) * ... * (1 + r_n)) ^ (1/n) - 1
        aum = portfolio.total_aum
        metrics['returns_annualized'] = (
                ((aum.iloc[-1] / aum.iloc[0])
                ** (1 / ((aum.index[-1] - aum.index[0]).days / 365)) - 1) * 100)

        ref = portfolio_buy_hold
        metrics['returns_annualized_buy_hold'] = (
                ((ref.iloc[-1] / ref.iloc[0])
                ** (1 / ((ref.index[-1] - ref.index[0]).days / 365)) - 1) * 100)

        # annualized volatility: std_dev * sqrt(periods/year)
        self.trading_days = 252
        metrics['volatility_ann'] = aum.pct_change().std() * np.sqrt(self.trading_days) * 100
        metrics['volatility_ann_buy_hold'] = ref.pct_change().std() * np.sqrt(self.trading_days) * 100

        # sharpe ratio: (rate - risk_free_rate) / volatility
        self.risk_free_rate = 0
        metrics['sharpe_ratio'] = (metrics['returns_annualized'] - self.risk_free_rate) / metrics['volatility_ann']
        metrics['sharpe_ratio_buy_hold'] = (metrics['returns_annualized_buy_hold'] - self.risk_free_rate) / metrics['volatility_ann_buy_hold']

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
        plt.grid(color = '#dee0df', linewidth = 0.1)
        plt.legend()
        plt.show()

    def print_trades(self):
        print("")
        for trade in self.strategy.trades:
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
