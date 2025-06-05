import os
from random import randint

from tqdm import tqdm
from model.Trade import Trade
from EngineUtils import *
import pandas as pd

class Engine:

    def __init__(self, id, strategy):

        self.id = id
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

        if self.metrics.size != 0:
            print('Engine already has results, skipping run ...')
            return

        # loop each bar
        for idx in tqdm(
            iterable = self.data.index,
            colour = 'BLUE',
            bar_format = '{percentage:3.0f}%|{bar:100}{r_bar}'):

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

        metrics = (
            analyze_config(self) +
            analyze_perf(self) +
            analyze_profit_factor(self) +
            analyze_max_drawdown(self) +
            analyze_expectancy(self))

        # persist as dict
        for metric in metrics:
            self.metrics[metric.name] = metric

    ''' serialize '''
    def save(self,
        id=0,
        dir_name='output'):

        slim_engine = {
            'id': self.id,
            'params': self.strategy.params,
            'metrics': self.metrics
        }

        # make directory, if needed
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        # create new binary
        # formatted_time = time.strftime('%Y%m%d_%H%M%S')
        filename = 'e' + str(id) + '.bin'
        path_filename = dir_name + '/' + filename
        filehandler = open(path_filename, 'wb')

        pickle.dump(slim_engine, filehandler)