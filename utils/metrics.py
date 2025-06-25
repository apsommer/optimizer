from datetime import timedelta

import numpy as np
import pandas as pd

from model.Metric import Metric

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

def get_engine_metrics(engine):

    # check trades exist
    num_trades = len(engine.trades)
    if num_trades == 0:
        print('Engine has no trades\n')
        return [ Metric('no_trades', None, None, 'Strategy: No trades') ]

    trades = engine.trades
    cash_series = engine.cash_series
    id = engine.id
    symbol = engine.strategy.ticker.symbol
    size = engine.strategy.size
    initial_cash = engine.initial_cash

    start_date = cash_series.index[0]
    end_date = cash_series.index[-1]
    days = (end_date - start_date).days
    candles = len(cash_series.index)

    # format timestamp
    start_date = format_timestamp(start_date)
    end_date = format_timestamp(end_date)

    cash = cash_series.iloc[-1]
    profit = cash - initial_cash
    trades_per_day = num_trades / days

    wins = [ trade.profit for trade in trades if trade.profit > 0 ]
    losses = [ trade.profit for trade in trades if 0 > trade.profit ]
    gross_profit = sum(wins)
    gross_loss = sum(losses)

    total_return = (profit / initial_cash) * 100
    annual_return = ((abs(cash) / initial_cash) ** (1 / (days / 365)) - 1) * 100
    if 0 > cash: annual_return = -annual_return

    if gross_loss == 0: profit_factor = np.inf
    elif gross_profit == 0: profit_factor = -np.inf
    else: profit_factor = gross_profit / abs(gross_loss)

    # calculate maximum drawdown
    initial_price = cash_series.iloc[0]
    roll_max = cash_series.cummax() # series, rolling maximum
    daily_drawdown = cash_series / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin() # series, rolling minimum

    drawdown = max_daily_drawdown.min() * initial_price
    drawdown_per_profit = (drawdown / profit) * 100

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

    # percent long, short
    longs = len([1 for trade in trades if trade.is_long])
    shorts = len([1 for trade in trades if trade.is_short])
    long_percent = round((longs / num_trades) * 100)
    short_percent = round((shorts / num_trades) * 100)

    params = engine.strategy.params

    return [

        # engine
        Metric('header', None, None, 'Engine:'),
        Metric('id', id, None, 'Id'),
        Metric('start_date', start_date, None, 'Start date'),
        Metric('end_date', end_date, None, 'End date'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
        Metric('symbol', symbol, None, 'Symbol'),
        Metric('size', size, None, 'Size'),
        Metric('initial_cash', initial_cash, 'USD', 'Initial cash'),

        # strategy
        Metric('strategy_header', None, None, 'Strategy:'),
        Metric('num_trades', num_trades, None, 'Trades'),
        Metric('profit_factor', profit_factor, None, 'Profit factor', '.2f'),
        Metric('drawdown', drawdown, 'USD', 'Drawdown'),
        Metric('profit', profit, 'USD', 'Profit'),
        Metric('trades_per_day', trades_per_day, None, 'Trades per day', '.2f'),
        Metric('gross_profit', gross_profit, 'USD', 'Gross profit'),
        Metric('gross_loss', gross_loss, 'USD', 'Gross loss'),
        Metric('total_return', total_return, '%', 'Total return'),
        Metric('annual_return', annual_return, '%', 'Annualized return'),
        Metric('drawdown_per_profit', drawdown_per_profit, '%', 'Drawdown per profit'),
        Metric('win_rate', win_rate, '%', 'Win rate'),
        Metric('loss_rate', loss_rate, '%', 'Loss rate'),
        Metric('average_win', average_win, 'USD', 'Average win'),
        Metric('average_loss', average_loss, 'USD', 'Average loss'),
        Metric('expectancy', expectancy, 'USD', 'Expectancy'),
        Metric('long_percent', long_percent, '%', 'Long'),
        Metric('short_percent', short_percent, '%', 'Short'),
        Metric('params', params, None, 'Params'),
    ]

def get_analyzer_metrics(analyzer):

    start_date = analyzer.data.index[0]
    end_date = analyzer.data.index[-1]
    num_engines = len(analyzer.engines)
    days = (analyzer.data.index[-1] - analyzer.data.index[0]).days
    candles = len(analyzer.data.index)

    # format timestamp
    start_date = format_timestamp(start_date)
    end_date = format_timestamp(end_date)

    return [
        Metric('header', None, None, 'Analyzer:'),
        Metric('id', analyzer.id, None, 'Id'),
        Metric('num_engines', num_engines, None, 'Engines'),
        Metric('start_date', start_date, None, 'Start date'),
        Metric('end_date', end_date, None, 'End date'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
    ]

def init_walk_forward_metrics(wfa):

    start_date = wfa.data.index[0]
    end_date = wfa.data.index[-1]
    candles = len(wfa.data.index)
    days = (end_date - start_date).days
    months = round(days / 30.437)
    in_sample = round(wfa.IS_len / 1440)
    out_of_sample = round(wfa.OS_len / 1440)

    # format timestamp
    start_date = format_timestamp(start_date)
    end_date = format_timestamp(end_date)

    # pretty
    candles = '{:,}'.format(candles)
    runs = str(wfa.runs) + ' + 1 last in-sample'
    in_sample = str(in_sample) + ' of ' + str(in_sample * (wfa.runs + 1))
    out_of_sample = str(out_of_sample) + ' of ' + str(out_of_sample * wfa.runs)

    return [
        Metric('header', None, None, 'Walk forward:'),
        Metric('months', months, None, 'Months'),
        Metric('start_date', start_date, None, 'Start date'),
        Metric('end_date', end_date, None, 'End date'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
        Metric('percent', wfa.percent, '%', 'Percent'),
        Metric('runs', runs, None, 'Runs'),
        Metric('in_sample', in_sample, None, 'In-sample days'),
        Metric('out_of_sample', out_of_sample, None, 'Out-of-sample days'),
    ]

def get_walk_forward_results_metrics(wfa):

    candles = wfa.OS_len
    start = wfa.data.index[-1]
    end = start + timedelta(minutes = candles)
    days = (end - start).days

    # format timestamp
    start = format_timestamp(start)
    end = format_timestamp(end)

    return [
        Metric('best_fitness', wfa.best_fitness.pretty, None, 'Fitness'),
        Metric('params', str(wfa.best_params), None, 'Params'),
        Metric('start', start, None, 'Start'),
        Metric('end', end, None, 'End'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
    ]

def format_timestamp(idx):
    return idx.strftime('%b %d, %Y, %H:%M')
