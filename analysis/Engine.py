import os
from operator import index

from sympy.printing.pretty.pretty_symbology import line_width
from tqdm import tqdm
from model.Metric import Metric
from model.Trade import Trade
from EngineUtils import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class Engine:

    def __init__(self, strategy):

        self.data = strategy.data
        self.strategy = strategy
        self.current_idx = -1
        self.trades = []
        self.cash_series = pd.Series(index=self.data.index)
        self.metrics = pd.Series()

        # init equity account
        margin_requirement = self.strategy.ticker.margin_requirement
        size = self.strategy.size
        initial_cash = margin_requirement * self.data.Close.iloc[0] * size
        self.initial_cash = round(initial_cash, -3)
        self.cash = self.initial_cash

    def run(self):

        # loop each bar
        for idx in tqdm(
            iterable = self.data.index,
            colour = 'BLUE',
            bar_format = '{percentage:3.0f}%|{bar:50}{r_bar}'):

            # set index todo refactor to single index, remove replication
            self.current_idx = idx
            self.strategy.current_idx = self.current_idx

            # execute strat
            self.strategy.on_bar()

            # fill order, if needed
            orders = self.strategy.orders
            if len(orders) > 0 and orders[-1].idx == self.current_idx:
                self._fill_order()

            # track cash balance
            self.cash_series[idx] = self.cash

        # analyze results
        self._analyze()

    def _fill_order(self):

        order = self.strategy.orders[-1]

        # exit open trade
        if order.sentiment == 'flat':

            trade = self.trades[-1]
            trade.exit_order = order
            self.cash += trade.profit
            return

        # enter new trade
        self.trades.append(
            Trade(
                side = order.sentiment,
                size = order.size,
                entry_order = order,
                exit_order = None))

    def _analyze(self):

        # config
        start_date = self.data.index[0]
        end_date = self.data.index[-1]
        days = (self.data.index[-1] - self.data.index[0]).days
        ticker = self.strategy.ticker.symbol
        size = self.strategy.size
        initial_cash = self.initial_cash

        # stats
        num_trades = len(self.trades)
        profit = self.cash - self.initial_cash
        max_drawdown = get_max_drawdown(self.cash_series)
        total_return = (abs(self.cash - self.initial_cash) / self.initial_cash ) * 100
        if self.initial_cash > self.cash: total_return = - total_return
        annualized_return = ((self.cash / self.initial_cash) ** (1 / (days / 365)) - 1) * 100
        profit_factor = get_profit_factor(self.trades)
        drawdown_per_profit = (max_drawdown / profit) * 100
        trades_per_day = num_trades / days
        winners = [trade.profit for trade in self.trades if trade.profit > 0]
        losers = [trade.profit for trade in self.trades if 0 >= trade.profit]
        win_rate = (len(winners) / num_trades) * 100
        average_win = sum(winners) / len(winners)
        loss_rate = (len(losers) / num_trades) * 100
        average_loss = sum(losers) / len(losers)
        expectancy = ((win_rate / 100) * average_win) - ((loss_rate / 100) * average_loss)

        metrics = [

            Metric('config_header', None, None, 'Config:'),
            Metric('start_date', start_date, None, 'Start Date'),
            Metric('end_date', end_date, None, 'End Date'),
            Metric('days', days, None, 'Number of Days'),
            Metric('ticker', ticker, None, 'Ticker'),
            Metric('size', size, None, 'Size'),
            Metric('initial_cash', initial_cash, 'USD', 'Initial Cash'),

            Metric('strategy_header', None, None, 'Strategy:'),
            Metric('num_trades', num_trades, None, 'Number of Trades'),
            Metric('profit_factor', profit_factor, None, 'Profit Factor', '.2f'),
            Metric('trades_per_day', trades_per_day, None, 'Trades per Day', '.2f'),
            Metric('profit', profit, 'USD', 'Profit'),
            Metric('max_drawdown', max_drawdown, 'USD', 'Maximum Drawdown'),
            Metric('average_win', average_win, 'USD', 'Average Win'),
            Metric('average_loss', average_loss, 'USD', 'Average Loss'),
            Metric('expectancy', expectancy, 'USD', 'Expectancy'),
            Metric('total_return', total_return, '%', 'Total Return'),
            Metric('annualized_return', annualized_return, '%', 'Annualized Return'),
            Metric('drawdown_per_profit', drawdown_per_profit, '%', 'Drawdown Percentage'),
            Metric('win_rate', win_rate, '%', 'Win Rate'),
            Metric('loss_rate', loss_rate, '%', 'Loss Rate'),
        ]

        for metric in metrics:
            self.metrics[metric.name] = metric

    def plot_equity(self):

        # init figure
        cash_series = self.cash_series
        init_figure(1, cash_series)

        # split cash balance into profit and loss
        pos, neg = [], []
        for balance in cash_series:

            over = balance >= self.initial_cash
            under = balance < self.initial_cash
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

        # initial cash
        initial_cash_df = pd.DataFrame(
            data = { 'initial_cash': self.initial_cash },
            index = cash_series.index)
        plt.plot(initial_cash_df, color = 'black')

        # buy and hold reference
        buy_hold = (self.data.Close - self.data.Open.iloc[0]) * self.strategy.ticker.tick_value + self.initial_cash
        plt.plot(buy_hold,  color = '#3C3C3C')

        # add series
        plt.plot(pos_df, color = 'green')
        plt.plot(neg_df, color = 'red')

        plt.autoscale(axis='y')

        # show
        plt.tight_layout()
        plt.show(block=False)

    def plot_trades(self):

        # init figure
        close = self.data.Close
        init_figure(2, close)

        # plot underlying
        plt.plot(close, color = '#3C3C3C')

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

            color = 'blue' # long
            if sentiment == 'short': color = 'aqua'

            plt.plot(trade_df, color)
            plt.plot(entry_idx, entry_price, color=color, marker='o', markersize=5)
            plt.plot(exit_idx, exit_price, color=color, marker='o', markersize=10)

        # show
        plt.tight_layout()
        plt.show(block=True)

    def print_trades(self):
        for trade in self.trades:
            print(trade)

    def print_metrics(self):

        for metric in self.metrics:

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

    ''' serialize '''
    def save_engine(self, id, name):

        package = {
            'trades': self.trades,
            'cash_series': self.cash_series,
            'metrics': self.metrics,
            'strategy_params': None # todo
        }

        # make directory, if needed
        if not os.path.exists(name):
            os.mkdir(name)

        # create new binary
        # formatted_time = time.strftime('%Y%m%d_%H%M%S')
        filename = 'e' + str(id) + '.bin'
        path_filename = name + '/' + filename
        filehandler = open(path_filename, 'wb')

        pickle.dump(package, filehandler)