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

    def run(self):

        # progress bar attributes
        isFirstProcess = '0' == multiprocessing.current_process().name

        for idx in tqdm(
            disable = not isFirstProcess,
            leave = False,
            position = 1,
            iterable = self.data.index,
            colour = aqua,
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

        # analyze results
        self.analyze()

    def fill_order(self):

        # get last order, and last trade
        order = self.strategy.orders[-1]
        if len(self.trades) == 0: trade = None
        else: trade = self.trades[-1]

        # enter new trade
        if trade is None or trade.is_closed:
            self.trades.append(
                Trade(
                    id = len(self.trades) + 1,
                    side = order.sentiment,
                    size = order.size,
                    entry_order = order,
                    exit_order = None))
            return

        # close open order
        trade.exit_order = order
        self.cash += trade.profit

        # flip, enter new trade
        if order.comment == 'flip':
            entry_order = self.strategy.orders[-2]
            self.trades.append(
                Trade(
                    id = len(self.trades) + 1,
                    side = entry_order.sentiment,
                    size = entry_order.size,
                    entry_order = entry_order,
                    exit_order = None))

    def analyze(self):

        # create metrics
        self.metrics = get_engine_metrics(self)

        # tag all metrics with engine id
        for metric in self.metrics: metric.id = self.id

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

    ####################################################################################################################

    def print_metrics(self):
        print_metrics(self.metrics)

    def print_trades(self):

        show_last = 1000
        trades = self.trades

        # header
        print('\nTrades:')
        print('\t\t\t\t\t\tclose\tprofit\tcomment')
        if len(trades) > show_last:
            print('\t...')

        for trade in trades[-show_last:]:
            print(trade)

        print()

    def plot_trades(self, shouldShow = False):

        # init
        ax = self.strategy.plot(
            title = f'{self.id}: Trades')

        # candlestick ohlc
        data = self.data
        fplt.candlestick_ochl(
            data[['Open', 'Close', 'High', 'Low']],
            ax = ax)

        # init dataframe plot entities
        entities = pd.DataFrame(
            index = data.index,
            dtype = float,
            columns = [
                'long_entry',
                'long_trade',
                'short_entry',
                'short_trade'
                'profit_exit',
                'loss_exit'])

        for trade in tqdm(
                iterable = self.trades,
                colour = green,
                bar_format = '        Plot:           {percentage:3.0f}%|{bar:100}{r_bar}'):

            # entry
            entry_idx = trade.entry_order.idx
            entry_price = trade.entry_order.price
            entry_bar = trade.entry_order.bar_index
            if trade.is_long: entities.loc[entry_idx, 'long_entry'] = entry_price
            else: entities.loc[entry_idx, 'short_entry'] = entry_price

            # exit
            exit_idx = trade.exit_order.idx
            exit_price = trade.exit_order.price
            exit_bar = trade.exit_order.bar_index
            profit = trade.profit
            if profit > 0:
                entities.loc[exit_idx, 'profit_exit'] = exit_price
                entities.loc[exit_idx, 'loss_exit'] = np.nan
            else:
                entities.loc[exit_idx, 'profit_exit'] = np.nan
                entities.loc[exit_idx, 'loss_exit'] = exit_price

            # build trade line
            timestamps = pd.date_range(
                start=entry_idx,
                end=exit_idx,
                freq='1min')
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

        marker_size = 3
        line_width = 7

        # entries
        # fplt.plot(entities['long_entry'], style='o', width = marker_size, color=blue, ax=ax)
        # fplt.plot(entities['short_entry'], style='o', width = marker_size, color=aqua, ax=ax)

        # exits
        fplt.plot(entities['profit_exit'], style='o', width = marker_size, color=green, ax=ax)
        fplt.plot(entities['loss_exit'], style='o', width = marker_size, color=red, ax=ax)

        # trades
        fplt.plot(entities['long_trade'], color=blue, width= line_width, ax=ax)
        fplt.plot(entities['short_trade'], color=aqua, width = line_width, ax=ax)

        if shouldShow: fplt.show()

    def plot_equity(self):

        ax = init_plot(1, f'{self.id}: Equity')

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