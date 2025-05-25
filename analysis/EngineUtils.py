import pickle
import numpy as np
import pandas as pd
from analysis.Engine import Engine
from model.Metric import Metric


def get_max_drawdown(prices):

    initial_price = prices.iloc[0]
    roll_max = prices.cummax() # series, rolling maximum
    daily_drawdown = prices / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin() # series, rolling minimum
    return max_daily_drawdown.min() * initial_price

def get_profit_factor(trades):

    wins = [trade.profit for trade in trades if trade.profit > 0]
    losses = [trade.profit for trade in trades if trade.profit < 0]
    total_wins = sum(wins)
    total_losses = -sum(losses)
    if total_losses > total_wins: return np.nan
    return total_wins / total_losses

def get_config_metrics(engine):

    start_date = engine.data.index[0]
    end_date = engine.data.index[-1]
    days = (engine.data.index[-1] - engine.data.index[0]).days
    ticker = engine.strategy.ticker.symbol
    size = engine.strategy.size
    initial_cash = engine.initial_cash

    return [
        Metric('config_header', None, None, 'Config:'),
        Metric('start_date', start_date, None, 'Start date'),
        Metric('end_date', end_date, None, 'End date'),
        Metric('days', days, None, 'Number of days'),
        Metric('ticker', ticker, None, 'Ticker'),
        Metric('size', size, None, 'Size'),
        Metric('initial_cash', initial_cash, 'USD', 'Initial cash')]

def get_perf_metrics(engine):

    days = (engine.data.index[-1] - engine.data.index[0]).days
    num_trades = len(engine.trades)
    profit = engine.cash - engine.initial_cash
    max_drawdown = get_max_drawdown(engine.cash_series)
    profit_factor = get_profit_factor(engine.trades)

    total_return = (abs(engine.cash - engine.initial_cash) / engine.initial_cash) * 100
    if engine.initial_cash > engine.cash: total_return = -total_return

    if 0 > engine.cash: annualized_return = np.nan
    else: annualized_return = ((engine.cash / engine.initial_cash) ** (1 / (days / 365)) - 1) * 100

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

def get_expectancy_metrics(engine):

    trades = engine.trades
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


''' deserialize '''
def load_engine(id, name, strategy):

    filename = 'e' + str(id) + '.bin'
    path_filename = name + '/' + filename
    filehandler = open(path_filename, 'rb')
    slim_engine = pickle.load(filehandler)

    engine = Engine(strategy)
    engine.trades = slim_engine['trades']
    engine.cash_series = pd.Series(
        data = slim_engine['cash_series'],
        index = strategy.data.index)
    engine.metrics = slim_engine['metrics']
    # todo engine strategy_params ...

    return engine
