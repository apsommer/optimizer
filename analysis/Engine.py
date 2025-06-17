import multiprocessing
import os
import pickle

from tqdm import tqdm

from utils.metrics import *
from model.Trade import Trade
import pandas as pd

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

    def run(self):

        # check if engine already ran
        if self.metrics:
            print('Engine already has results, skipping run ...')
            return

        # determine which process (core) is running
        isFirstProcess = 'ForkPoolWorker-1' == multiprocessing.current_process().name

        # loop each bar
        for idx in tqdm(
            disable = not isFirstProcess,
            leave = False,
            position = 1,
            iterable = self.data.index,
            colour = '#42f5f5',
            bar_format = '        {percentage:3.0f}%|{bar:92}{r_bar}'):

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

        self.metrics = get_engine_metrics(self)

        # tag all metrics with engine id
        for metric in self.metrics:
            metric.id = self.id

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

    ''' serialize '''
    def save(self, path, isFull):

        # out-of-sample
        if isFull:
            result = {
                'id': self.id,
                'params': self.strategy.params,
                'metrics': self.metrics,
                'trades': self.trades,
                'cash_series': self.cash_series
            }

        # in-sample
        else:
            result = {
                'id': self.id,
                'params': self.strategy.params,
                'metrics': self.metrics,
                # 'trades': self.trades,
                # 'cash_series': self.cash_series
            }

        # make directory, if needed
        if not os.path.exists(path):
            os.makedirs(path)

        # create new binary
        filename = str(self.id) + '.bin'
        path_filename = path + '/' + filename

        filehandler = open(path_filename, 'wb')
        pickle.dump(result, filehandler)
