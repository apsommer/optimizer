from tqdm import tqdm
from model.Trade import Trade
from EngineUtils import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class Engine:

    def __init__(self):
        self.data = None
        self.strategy = None
        self.current_idx = -1
        self.initial_cash = 0
        self.cash = self.initial_cash
        self.trades = [ ]
        self.cash_series = { } # todo refactor to series
        self.stats = { }

    def run(self):

        # init
        margin_requirement = self.strategy.ticker.margin_requirement
        size = self.strategy.size
        self.initial_cash = 10e3 # margin_requirement * self.first_bar_close
        self.cash = self.initial_cash
        self.strategy.data = self.data

        # loop each bar
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

            # track cash balance
            self.cash_series[idx] = self.cash

        return self._get_stats()

    def _fill_order(self):

        order = self.strategy.orders[-1]
        profit = 0

        if order.sentiment == 'long' or order.sentiment == 'short':
            trade = Trade(
                side = order.sentiment, # long, short
                size = order.size,
                entry_order = order,
                exit_order = None)
            self.trades.append(trade)

        elif order.sentiment == 'flat':
            open_trade = self.trades[-1]
            open_trade.exit_order = order
            profit = open_trade.profit

        self.cash += profit

    def _get_stats(self):

        stats = { }
        # trading_days = 252
        # risk_free_rate = 0
        days = (self.data.index[-1] - self.data.index[0]).days

        # general
        stats['Config:'] = ''
        stats['start_date'] = str(self.data.index[0])
        stats['end_date'] = str(self.data.index[-1])
        stats['days'] = days
        stats['ticker'] = self.strategy.ticker.symbol
        stats['size'] = self.strategy.size
        stats['initial_cash [$]'] = self.initial_cash

        # todo check volatility and sharpe ratio

        # strategy
        cash_df = pd.DataFrame({'cash': self.cash_series})
        num_trades = len(self.trades)
        profit = self.cash - self.initial_cash
        max_drawdown = get_max_drawdown(cash_df['cash'])
        total_return = (abs(self.cash - self.initial_cash) / self.initial_cash ) * 100
        if self.initial_cash > self.cash: total_return = - total_return
        annualized_return = ((self.cash / self.initial_cash) ** (1 / (days / 365)) - 1) * 100
        # volatility = cash_df['cash'].pct_change().std() * np.sqrt(trading_days) * 100
        winners = [trade.profit for trade in self.trades if trade.profit > 0]
        losers = [trade.profit for trade in self.trades if 0 >= trade.profit]
        win_rate = len(winners) / num_trades
        average_win = sum(winners) / len(winners)
        loss_rate = len(losers) / num_trades
        average_loss = sum(losers) / len(losers)
        expectancy = (win_rate * average_win) - (loss_rate * average_loss)

        stats['Strategy:'] = ''
        stats['num_trades'] = num_trades
        stats['profit_factor'] = get_profit_factor(self.trades)
        stats['profit [$]'] = profit
        stats['total_return [%]'] = total_return
        stats['annualized_return [%]'] = annualized_return
        stats['max_drawdown [$]'] = max_drawdown
        stats['drawdown/profit [%]'] = (max_drawdown / profit) * 100
        # stats['annualized_volatility [%]'] = volatility
        # stats['sharpe'] = (annualized_return - risk_free_rate) / volatility
        stats['trades/day'] = num_trades / days
        stats['win_rate [%]'] = win_rate * 100
        stats['average_win [$]'] = average_win
        stats['loss_rate [%]'] = loss_rate * 100
        stats['average_loss [$]'] = average_loss
        stats['expectancy [$]'] = expectancy

        # reference simple "buy and hold"
        entry_price_bh = self.data.iloc[0]['Close']
        exit_price_bh = self.data.iloc[-1]['Close']
        buy_hold_df = self.initial_cash + self.strategy.ticker.tick_value * (self.data.Close - entry_price_bh)
        profit_buy_hold = buy_hold_df.iloc[-1] - buy_hold_df.iloc[0]
        total_return_buy_hold = (abs(profit_buy_hold) / buy_hold_df.iloc[0]) * 100
        if entry_price_bh > exit_price_bh: total_return_buy_hold = - total_return_buy_hold
        annualized_return_buy_hold = ((buy_hold_df.iloc[-1] / buy_hold_df.iloc[0]) ** (1 / (days / 365)) - 1) * 100
        # volatility_buy_hold = buy_hold_df.pct_change().std() * np.sqrt(trading_days) * 100

        stats['Buy & Hold:'] = ''
        stats['profit_bh [$]'] = profit_buy_hold
        stats['total_return_bh [%]'] = total_return_buy_hold
        stats['annualized_return_bh [%]'] = annualized_return_buy_hold
        stats['max_drawdown_bh [%]'] = get_max_drawdown(buy_hold_df)
        # stats['volatility_ann_bh [%]'] = volatility_buy_hold
        # stats['sharpe_ratio_bh'] = (annualized_return_buy_hold - risk_free_rate) / volatility_buy_hold

        # persist df for plots
        self.cash_df = cash_df
        self.buy_hold_df = buy_hold_df
        self.stats = stats

        return stats

    def plot_equity(self):

        # init figure
        fig_id = 1
        cash_series = self.cash_df['cash']
        init_figure(
            fig_id=fig_id,
            data=self.buy_hold_df)

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

        # add series
        plt.plot(pos_df, color = 'green', label='equity (pos)')
        plt.plot(neg_df, color = 'red', label='equity (neg)')
        plt.plot(self.buy_hold_df, color ='#3C3C3C', label='buy/hold')

        # show
        plt.legend(
            facecolor='#0D0B1A',
            frameon=False)
        plt.tight_layout()
        plt.show(block=False)

    def plot_trades(self):

        # init figure
        fig_id = 2
        close = self.data.Close
        init_figure(
            fig_id=fig_id,
            data=close)

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

            # set color
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
        for trade in self.trades:
            print(trade)

def print_stats(stats):
    for stat, value in stats.items():
        if ":" in stat: print(stat) # header
        else: print("\t{}: {}".format(stat, value)) # stat
