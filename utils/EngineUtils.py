from datetime import timedelta

import numpy as np
import pandas as pd

from model.Metric import Metric

def get_profit_factor_metrics(engine):

    # extract wins and losses
    trades = engine.trades
    wins = [trade.profit for trade in trades if trade.profit > 0]
    losses = [trade.profit for trade in trades if 0 > trade.profit]

    # gross p&l
    gross_profit = sum(wins)
    gross_loss = -sum(losses)

    # profit factor
    if gross_loss == 0: profit_factor = np.inf
    elif gross_profit == 0: profit_factor = -np.inf
    else: profit_factor = gross_profit / gross_loss

    return [
        Metric('gross_profit', gross_profit, 'USD', 'Gross profit'),
        Metric('gross_loss', gross_loss, 'USD', 'Gross loss'),
        Metric('profit_factor', profit_factor, None, 'Profit factor', '.2f') ]

def get_expectancy_metrics(engine):

    # extract wins and losses
    trades = engine.trades
    wins = [trade.profit for trade in trades if trade.profit > 0]
    losses = [trade.profit for trade in trades if 0 > trade.profit]

    # check trades exist
    num_trades = len(trades)
    if num_trades == 0:
        return []

    # last trade open
    last_trade = trades[-1]
    if last_trade.exit_order is None:
        num_trades -= 1

    # wins
    num_wins = len(wins)
    win_rate = (num_wins / num_trades) * 100
    if num_wins == 0: average_win = 0
    else: average_win = sum(wins) / num_wins

    # losses
    num_losses = len(losses)
    loss_rate = (num_losses / num_trades) * 100
    if num_losses == 0: average_loss = 0
    else: average_loss = sum(losses) / len(losses)

    expectancy = ((win_rate / 100) * average_win) + ((loss_rate / 100) * average_loss)

    return [
        Metric('win_rate', win_rate, '%', 'Win rate'),
        Metric('loss_rate', loss_rate, '%', 'Loss rate'),
        Metric('average_win', average_win, 'USD', 'Average win'),
        Metric('average_loss', average_loss, 'USD', 'Average loss'),
        Metric('expectancy', expectancy, 'USD', 'Expectancy')]

def get_max_drawdown_metrics(engine):

    prices = engine.cash_series
    profit = engine.cash - engine.initial_cash
    initial_price = prices.iloc[0]
    roll_max = prices.cummax() # series, rolling maximum
    daily_drawdown = prices / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin() # series, rolling minimum
    max_drawdown = max_daily_drawdown.min() * initial_price
    drawdown_per_profit = (max_drawdown / profit) * 100

    return [
        Metric('max_drawdown', max_drawdown, 'USD', 'Maximum drawdown'),
        Metric('drawdown_per_profit', drawdown_per_profit, '%', 'Drawdown percentage')]

def get_engine_metrics(engine):

    id = engine.id
    start_date = engine.data.index[0]
    end_date = engine.data.index[-1]
    days = (engine.data.index[-1] - engine.data.index[0]).days
    candles = len(engine.data.index)
    ticker = engine.strategy.ticker.symbol
    size = engine.strategy.size
    initial_cash = engine.initial_cash

    return [
        Metric('config_header', None, None, 'Engine:'),
        Metric('id', id, None, 'Id'),
        Metric('start_date', start_date, None, 'Start date'),
        Metric('end_date', end_date, None, 'End date'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
        Metric('ticker', ticker, None, 'Ticker'),
        Metric('size', size, None, 'Size'),
        Metric('initial_cash', initial_cash, 'USD', 'Initial cash')]

def get_perf_metrics(engine):

    days = (engine.data.index[-1] - engine.data.index[0]).days

    if engine.trades[-1].is_open: num_trades = len(engine.trades) - 1
    else: num_trades = len(engine.trades)

    engine.cash = engine.cash_series.iloc[-1]
    profit = engine.cash - engine.initial_cash

    total_return = (abs(engine.cash - engine.initial_cash) / engine.initial_cash) * 100
    if engine.initial_cash > engine.cash: total_return = -total_return

    if 0 > engine.cash: annualized_return = np.nan
    else: annualized_return = ((engine.cash / engine.initial_cash) ** (1 / (days / 365)) - 1) * 100

    trades_per_day = num_trades / days

    return [
        Metric('strategy_header', None, None, 'Strategy:'),
        Metric('profit', profit, 'USD', 'Profit'),
        Metric('num_trades', num_trades, None, 'Trades'),
        Metric('trades_per_day', trades_per_day, None, 'Trades per day', '.2f'),
        Metric('total_return', total_return, '%', 'Total return'),
        Metric('annualized_return', annualized_return, '%', 'Annualized return')]


def get_analyzer_params_metrics(analyzer, id):

    params_title = '*[' + str(id) + ']'

    return [
        Metric('params', str(analyzer.params), None, params_title) ]

def get_walk_forward_params_metrics(walk_forward):

    candles = walk_forward.OS_len
    start = walk_forward.data.index[-1]
    end = start + timedelta(minutes = candles)
    days = (end - start).days

    return [
        Metric('params', str(walk_forward.params), None, 'Next params'),
        Metric('next_start', start, None, 'Next start'),
        Metric('next_end', end, None, 'Next end'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days')]

def get_analyzer_metrics(analyzer):

    start_date = analyzer.data.index[0]
    end_date = analyzer.data.index[-1]
    num_engines = len(analyzer.results)
    days = (analyzer.data.index[-1] - analyzer.data.index[0]).days
    candles = len(analyzer.data.index)

    return [
        Metric('header', None, None, 'Analyzer:'),
        Metric('id', analyzer.id, None, 'Id'),
        Metric('num_engines', num_engines, None, 'Engines'),
        Metric('start_date', start_date, None, 'Start date'),
        Metric('end_date', end_date, None, 'End date'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days')]

def get_analyzer_metric(analyzer, name, isMax):

    results = analyzer.results

    # isolate metric of interest
    _metrics = []
    for metrics in results:
        for metric in metrics:
            if metric.name == name:
                _metrics.append(metric)

    metric = sorted(
        _metrics,
        key = lambda it: it.value,
        reverse = isMax)[0]

    name = metric.name
    value = metric.value
    unit = metric.unit
    title = '[' + str(metric.id) + '] (Max) ' + metric.title
    formatter = metric.formatter
    id = metric.id

    return [
        Metric(name, value, unit, title, formatter, id) ]

def get_walk_forward_metrics(walk_forward):

    return [
        Metric('header', None, None, 'Walk forward:'),
        Metric('path', walk_forward.path, None, 'Path'),
        Metric('percent', walk_forward.percent, None, 'Percent'),
        Metric('runs', walk_forward.runs, None, 'Runs') ]

def print_metrics(metrics):

    for metric in metrics:

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
