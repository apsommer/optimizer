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

def get_expectancy_metrics(trades):

    num_trades = len(trades)
    winners = [trade.profit for trade in trades if trade.profit > 0]
    losers = [trade.profit for trade in trades if 0 >= trade.profit]

    if len(winners) == 0 or len(losers) == 0:
        return []

    win_rate = (len(winners) / num_trades) * 100
    average_win = sum(winners) / len(winners)
    loss_rate = (len(losers) / num_trades) * 100
    average_loss = sum(losers) / len(losers)
    expectancy = ((win_rate / 100) * average_win) - ((loss_rate / 100) * average_loss)

    return [
        Metric('win_rate', win_rate, '%', 'Win rate'),
        Metric('loss_rate', loss_rate, '%', 'Loss rate'),
        Metric('average_win', average_win, 'USD', 'Average win'),
        Metric('average_loss', average_loss, 'USD', 'Average loss'),
        Metric('expectancy', expectancy, 'USD', 'Expectancy'),
    ]

def get_profit_factor(trades):

    wins = [trade.profit for trade in trades if trade.profit > 0]
    losses = [trade.profit for trade in trades if trade.profit < 0]
    total_wins = sum(wins)
    total_losses = -sum(losses)
    if total_losses > total_wins: return np.nan
    return total_wins / total_losses

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
