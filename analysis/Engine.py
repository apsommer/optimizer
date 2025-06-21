import multiprocessing
import os
import pickle

from tqdm import tqdm

from model.Fitness import Fitness
from utils.constants import *
from utils.metrics import *
from model.Trade import Trade
import pandas as pd
import finplot as fplt

from utils.utils import *

class Engine:

    def __init__(self, id, strategy):

        # allow blank engine for rebuild
        if strategy is None: return

        self.id = id
        self.data = strategy.data
        self.strategy = strategy
        self.current_idx = -1
        self.trades = []
        self.cash_series = pd.Series(index=self.data.index)
        self.metrics = []

        # init equity account
        margin = self.strategy.ticker.margin
        size = self.strategy.size
        initial_cash = margin * self.data.Close.iloc[0] * size
        self.initial_cash = round(initial_cash, -3)
        self.cash = self.initial_cash

    def run(self, showProgress=False):

        # progress bar attributes
        isFirstProcess = '0' == multiprocessing.current_process().name
        if showProgress: position = 0
        else: position = 1

        for idx in tqdm(
            disable = not isFirstProcess and not showProgress,
            leave = False,
            position = position,
            iterable = self.data.index,
            colour = '#42f5f5',
            bar_format = '                        {percentage:3.0f}%|{bar:100}{r_bar}'):

            # set index
            self.current_idx = idx
            self.strategy.current_idx = self.current_idx

            # execute strat
            self.strategy.on_bar()

            # fill order, if needed
            orders = self.strategy.orders
            if len(orders) > 0 and orders[-1].idx == self.current_idx:
                self.fill_order()

            # track cash balance
            self.cash_series[idx] = self.cash

            # todo temp
            # print(self.cash_series[idx])

        # analyze results
        self.analyze()

    def fill_order(self):

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
                id = len(self.trades) + 1,
                side = order.sentiment,
                size = order.size,
                entry_order = order,
                exit_order = None))

    def analyze(self):

        # create metrics
        self.metrics = get_engine_metrics(self)

        # tag all metrics with engine id
        for metric in self.metrics: metric.id = self.id

    def print_trades(self):

        show_last = 3
        trades = self.trades

        # header
        print('\nTrades:')
        print('\t\t\t\t\t\tclose\tprofit')
        if len(trades) > show_last:
            print('\t...')

        for trade in trades[-show_last:]:
            print(trade)

        print()

    def plot_trades(self):

        ax = init_plot(0, 'Trades')

        # candlestick ohlc
        data = self.data
        fplt.candlestick_ochl(
            data[['Open', 'Close', 'High', 'Low']],
            ax=ax)  # , draw_body=False, draw_shadow=False)

        # cloud
        # low = fplt.plot(data.Low, color=black, width=0, ax=ax)
        # high = fplt.plot(data.High, color=black, width=0, ax=ax)
        # fplt.fill_between(low, high, color = light_gray)

        # init dataframe plot entities
        entities = pd.DataFrame(
            index=data.index,
            dtype=float,
            columns=[
                'long_entry',
                'long_trade',
                'short_entry',
                'short_trade'
                'profit_exit',
                'loss_exit'])

        for trade in tqdm(
                iterable=self.trades,
                colour=green,
                bar_format='        Plot:           {percentage:3.0f}%|{bar:100}{r_bar}'):

            # entry
            entry_idx = trade.entry_order.idx
            entry_price = trade.entry_order.price
            entry_bar = trade.entry_order.bar_index

            if trade.is_long:
                entities.loc[entry_idx, 'long_entry'] = entry_price
            else:
                entities.loc[entry_idx, 'short_entry'] = entry_price

            # exit
            exit_idx = trade.exit_order.idx
            exit_price = trade.exit_order.price
            exit_bar = trade.exit_order.bar_index
            profit = trade.profit

            if profit > 0:
                entities.loc[exit_idx, 'profit_exit'] = exit_price
            else:
                entities.loc[exit_idx, 'loss_exit'] = exit_price

            # linear interpolate between entry and exit
            timestamps = pd.date_range(
                start=entry_idx,
                end=exit_idx,
                freq='1min')

            # build trade line
            slope = (exit_price - entry_price) / (exit_bar - entry_bar)
            trade_bar = 0
            for timestamp in timestamps:

                # prevent gaps in plot
                if timestamp not in data.index: continue

                # y = mx + b
                price = slope * trade_bar + entry_price
                if trade.is_long:
                    entities.loc[timestamp, 'long_trade'] = price
                    entities.loc[timestamp, 'short_trade'] = np.nan
                else:
                    entities.loc[timestamp, 'long_trade'] = np.nan
                    entities.loc[timestamp, 'short_trade'] = price

                trade_bar += 1

        # entries
        fplt.plot(entities['long_entry'], style='o', color=blue, ax=ax)
        fplt.plot(entities['short_entry'], style='o', color=aqua, ax=ax)

        # exits
        fplt.plot(entities['profit_exit'], style='o', color=green, ax=ax)
        fplt.plot(entities['loss_exit'], style='o', color=red, ax=ax)

        # trades
        fplt.plot(entities['long_trade'], color=blue, ax=ax)
        fplt.plot(entities['short_trade'], color=aqua, ax=ax)

        # fplt.show()

    def plot_equity(self):

        ax = init_plot(1, 'Equity')

        # buy and hold
        size = self.strategy.size
        point_value = self.strategy.ticker.point_value
        delta_df = self.data.Close - self.data.Close.iloc[0]
        buy_hold = size * point_value * delta_df + self.initial_cash
        fplt.plot(buy_hold, color=dark_gray, ax=ax)

        # initial cash
        initial_cash = [ self.initial_cash for idx in self.data.index ]
        fplt.plot(initial_cash, color=dark_gray, ax=ax)

        # equity
        fplt.plot(self.cash_series, ax = ax)

        fplt.show()

    def print_metrics(self):
        print_metrics(self.metrics)

    ''' serialize '''
    def save(self, path, isFull):

        # out-of-sample
        if isFull: bundle = {
            'id': self.id,
            'params': self.strategy.params,
            'metrics': self.metrics,
            'trades': self.trades,
            'cash_series': self.cash_series
        }

        # in-sample
        else: bundle = {
            'id': self.id,
            'params': self.strategy.params,
            'metrics': self.metrics
        }

        save(
            bundle = bundle,
            filename = str(self.id),
            path = path)
