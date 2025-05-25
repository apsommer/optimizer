import os
from tqdm import tqdm
from model.Metric import Metric
from model.Trade import Trade
from EngineUtils import *
import pandas as pd

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

        if self.metrics.size != 0:
            print('Engine already has results, skipping run ...')
            return

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
                side = order.sentiment,
                size = order.size,
                entry_order = order,
                exit_order = None))

    def analyze(self):

        metrics = (
            self.get_config_metrics() +
            self.get_perf_metrics() +
            self.get_expectancy_metrics())

        # persist as dict
        for metric in metrics:
            self.metrics[metric.name] = metric

    def get_config_metrics(self):

        start_date = self.data.index[0]
        end_date = self.data.index[-1]
        days = (self.data.index[-1] - self.data.index[0]).days
        ticker = self.strategy.ticker.symbol
        size = self.strategy.size
        initial_cash = self.initial_cash

        return [
            Metric('config_header', None, None, 'Config:'),
            Metric('start_date', start_date, None, 'Start date'),
            Metric('end_date', end_date, None, 'End date'),
            Metric('days', days, None, 'Number of days'),
            Metric('ticker', ticker, None, 'Ticker'),
            Metric('size', size, None, 'Size'),
            Metric('initial_cash', initial_cash, 'USD', 'Initial cash')]

    def get_perf_metrics(self):

        days = (self.data.index[-1] - self.data.index[0]).days
        num_trades = len(self.trades)
        profit = self.cash - self.initial_cash
        max_drawdown = get_max_drawdown(self.cash_series)
        profit_factor = get_profit_factor(self.trades)

        total_return = (abs(self.cash - self.initial_cash) / self.initial_cash) * 100
        if self.initial_cash > self.cash: total_return = -total_return

        if 0 > self.cash: annualized_return = np.nan
        else: annualized_return = ((self.cash / self.initial_cash) ** (1 / (days / 365)) - 1) * 100

        drawdown_per_profit = (max_drawdown / profit) * 100
        trades_per_day = num_trades / days

        return [
            Metric('strategy_header', None, None, 'Strategy:'),
            Metric('profit', profit, 'USD', 'Profit'),
            Metric('num_trades', num_trades, None, 'Number of trades'),
            Metric('profit_factor', profit_factor, None, 'Profit factor', '.2f'),
            Metric('max_drawdown', max_drawdown, 'USD', 'Maximum drawdown'),
            Metric('trades_per_day', trades_per_day, None, 'Trades per day', '.2f'),
            Metric('total_return', total_return, '%', 'Total return'),
            Metric('annualized_return', annualized_return, '%', 'Annualized return'),
            Metric('drawdown_per_profit', drawdown_per_profit, '%', 'Drawdown percentage')]

    def get_expectancy_metrics(self):

        trades = self.trades
        num_trades = len(trades)
        winners = [trade.profit for trade in trades if trade.profit > 0]
        losers = [trade.profit for trade in trades if 0 >= trade.profit]

        if len(winners) == 0 or len(losers) == 0:
            return []

        win_rate = (len(winners) / num_trades) * 100
        average_win = sum(winners) / len(winners)
        loss_rate = (len(losers) / num_trades) * 100
        average_loss = sum(losers) / len(losers)
        expectancy = ((win_rate / 100) * average_win) + ((loss_rate / 100) * average_loss)

        return [
            Metric('win_rate', win_rate, '%', 'Win rate'),
            Metric('loss_rate', loss_rate, '%', 'Loss rate'),
            Metric('average_win', average_win, 'USD', 'Average win'),
            Metric('average_loss', average_loss, 'USD', 'Average loss'),
            Metric('expectancy', expectancy, 'USD', 'Expectancy')]

    def print_trades(self):
        for trade in self.trades:
            print(trade)

    ''' serialize '''
    def save(self, id, name):

        # todo reduce this to just metrics and strategy_params
        slim_engine = {
            'metrics': self.metrics,
            'params': self.strategy.params
        }

        # make directory, if needed
        if not os.path.exists(name):
            os.mkdir(name)

        # create new binary
        # formatted_time = time.strftime('%Y%m%d_%H%M%S')
        filename = 'e' + str(id) + '.bin'
        path_filename = name + '/' + filename
        filehandler = open(path_filename, 'wb')

        pickle.dump(slim_engine, filehandler)