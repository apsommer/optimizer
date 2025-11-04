import math
from datetime import timedelta

from rich.console import Console
from rich.padding import Padding
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

import numpy as np
from model.Metric import Metric
from utils.utils import format_timestamp, unpack

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

def display_progress_bar(metrics):

    profit = round(next(metric for metric in metrics if metric.name == 'profit').value)
    pf = round(next(metric for metric in metrics if metric.name == 'profit_factor').value, 2)
    trades = next(metric for metric in metrics if metric.name == 'num_trades').value
    params = next(metric for metric in metrics if metric.name == 'params').value

    return f'{pf} / {trades}, {profit}'

def get_engine_metrics(engine):

    # check trades exist
    num_trades = len(engine.trades)
    if num_trades == 0:
        return [
            Metric('no_trades', None, None, f'Engine {engine.id} has no trades'),
            Metric('profit', 0, 'USD', 'Profit')
        ]

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
    profit_per_day = profit / days

    wins = [ trade.profit for trade in trades if trade.profit > 0 ]
    losses = [ trade.profit for trade in trades if 0 > trade.profit ]
    gross_profit = sum(wins)
    gross_loss = sum(losses)

    total_return = (profit / initial_cash) * 100
    annual_return = ((cash / initial_cash) ** (1 / (days / 365)) - 1) * 100
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
    drawdown_per_day = drawdown / days

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
    longs = [trade for trade in trades if trade.is_long]
    shorts = [trade for trade in trades if trade.is_short]
    percent_long = round((len(longs) / num_trades) * 100)
    percent_short = round((len(shorts) / num_trades) * 100)

    # split trades in winners and losers
    profitable_longs = [trade.profit for trade in longs if trade.profit > 0]
    losing_longs = [trade.profit for trade in longs if 0 >= trade.profit]
    profitable_shorts = [trade.profit for trade in shorts if trade.profit > 0]
    losing_shorts = [trade.profit for trade in shorts if 0 > trade.profit]

    avg_win_longs = np.mean(profitable_longs)
    avg_loss_longs = np.mean(losing_longs)
    avg_win_shorts = np.mean(profitable_shorts)
    avg_loss_shorts = np.mean(losing_shorts)

    if len(longs) == 0: win_rate_long = np.nan
    else: win_rate_long = (len(profitable_longs) / len(longs)) * 100

    if len(shorts) == 0: win_rate_short = np.nan
    else: win_rate_short = (len(profitable_shorts) / len(shorts)) * 100

    # catch composite with final in-sample not profitable
    params = engine.strategy.params
    if params is None:
        params = 'Last in-sample analyzer not profitable!'

    # calculate linear correlation
    bar_indices = np.arange(len(cash_series)).reshape(-1, 1)
    adjusted_cash_series = np.array(cash_series - initial_cash)

    regression = (
        LinearRegression(fit_intercept = False).fit(
            X = bar_indices, # todo simplify as cash_series.index?
            y = adjusted_cash_series))

    line = regression.predict(bar_indices)
    mse = mean_squared_error(adjusted_cash_series, line)
    correlation = math.sqrt(mse)

    # pretty
    candles = '{:,}'.format(candles)

    # negative for fitness optimization
    num_losses = -num_losses
    correlation = -correlation

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
        Metric('drawdown_per_day', drawdown_per_day, 'USD', 'Drawdown per day'),
        Metric('profit', profit, 'USD', 'Profit'),
        Metric('trades_per_day', trades_per_day, None, 'Trades per day', '.2f'),
        Metric('profit_per_day', profit_per_day, 'USD', 'Profit per day'),
        Metric('gross_profit', gross_profit, 'USD', 'Gross profit'),
        Metric('gross_loss', gross_loss, 'USD', 'Gross loss'),
        Metric('total_return', total_return, '%', 'Total return'),
        Metric('annual_return', annual_return, '%', 'Annualized return'),
        Metric('drawdown_per_profit', drawdown_per_profit, '%', 'Drawdown per profit'),
        Metric('num_wins', num_wins, None, 'Number of wins'),
        Metric('num_losses', num_losses, None, 'Number of losses'),
        Metric('win_rate', win_rate, '%', 'Win rate'),
        Metric('loss_rate', loss_rate, '%', 'Loss rate'),
        Metric('average_win', average_win, 'USD', 'Average win'),
        Metric('average_loss', average_loss, 'USD', 'Average loss'),
        Metric('expectancy', expectancy, 'USD', 'Expectancy'),
        Metric('correlation', correlation, 'USD', 'Linear correlation'),

        Metric('long_percent', percent_long, '%', 'Long'),
        Metric('short_percent', percent_short, '%', 'Short'),
        Metric('avg_win_longs', avg_win_longs, 'USD', 'Average win (long)'),
        Metric('avg_loss_longs', avg_loss_longs, 'USD', 'Average loss (long)'),
        Metric('avg_win_shorts', avg_win_shorts, 'USD', 'Average win (short)'),
        Metric('avg_loss_shorts', avg_loss_shorts, 'USD', 'Average loss (short)'),
        Metric('win_rate_long', win_rate_long, '%', 'Win rate (long)'),
        Metric('win_rate_short', win_rate_short, '%', 'Win rate (short)'),

        Metric('params', params, None, 'Params'),
    ]

def get_analyzer_metrics(analyzer):

    start_date = analyzer.data.index[0]
    end_date = analyzer.data.index[-1]
    num_engines = analyzer.opt.size

    # calculate percent profitable
    profitable = 0
    for id in np.arange(num_engines):
        profitable += next((1 for metric in analyzer.engine_metrics if metric.id == id), 0)
    profitable_percent = (profitable / num_engines) * 100

    days = (analyzer.data.index[-1] - analyzer.data.index[0]).days
    candles = len(analyzer.data.index)

    # format timestamp
    start_date = format_timestamp(start_date)
    end_date = format_timestamp(end_date)

    # pretty
    candles = '{:,}'.format(candles)

    return [
        Metric('header', None, None, 'Analyzer:'),
        Metric('id', analyzer.id, None, 'Id'),
        Metric('num_engines', num_engines, None, 'Engines'),
        Metric('profitable_percent', profitable_percent, '%', 'Profitable engines'),
        Metric('start_date', start_date, None, 'Start date'),
        Metric('end_date', end_date, None, 'End date'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
    ]

def init_walk_forward_metrics(wfa):

    # configuration
    id = wfa.id
    asset = wfa.parent_path.split('/')[-1].split('_')[0]
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

    opt = wfa.opt

    # pretty
    candles = '{:,}'.format(candles)
    runs = str(wfa.runs) + ' + 1 last in-sample'
    in_sample_days = str(in_sample) + ' of ' + str(in_sample * (wfa.runs + 1))
    out_of_sample_days = str(out_of_sample) + ' of ' + str(out_of_sample * wfa.runs)

    # fitness
    fitness = wfa.fitness.pretty

    return [
        Metric('header', None, None, 'Walk forward:'),
        Metric('id', id, None, 'Id'),
        Metric('asset', asset, None, 'Asset'),
        Metric('months', months, None, 'Months'),
        Metric('percent', wfa.percent, '%', 'Percent'),
        Metric('runs', runs, None, 'Runs'),
        Metric('in_sample_days', in_sample_days, None, 'In-sample days'),
        Metric('out_of_sample_days', out_of_sample_days, None, 'Out-of-sample days'),
        Metric('start_date', start_date, None, 'Start date'),
        Metric('end_date', end_date, None, 'End date'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
        Metric('fitness', fitness, None, 'Fitness'),
        Metric('opt', opt, None, 'Optimization'),
    ]

def get_walk_forward_results_metrics(wfa):

    candles = wfa.OS_len
    start = wfa.data.index[-1]
    end = start + timedelta(minutes = candles)
    days = (end - start).days

    # format timestamp
    start = format_timestamp(start)
    end = format_timestamp(end)

    # pretty
    best_fitness = wfa.best_fitness.pretty
    next_params = wfa.next_params.one_line
    candles = '{:,}'.format(candles)

    return [
        Metric('header', None, None, 'Solution:'),
        Metric('best_fitness', best_fitness, None, 'Best fitness'),
        Metric('next_params', next_params, None, 'Next params'),
        Metric('start', start, None, 'Start'),
        Metric('end', end, None, 'End'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
    ]

def init_genetic_metrics(genetic):

    start_date = genetic.data.index[0]
    end_date = genetic.data.index[-1]
    candles = len(genetic.data.index)
    days = (end_date - start_date).days
    months = round(days / 30.437)

    population_size = genetic.population_size
    generations = genetic.generations
    mutation_rate = genetic.mutation_rate * 100
    fitness = genetic.fitness.pretty
    cores = genetic.cores
    opt = genetic.opt

    # format timestamp
    start = format_timestamp(start_date)
    end = format_timestamp(end_date)

    # pretty
    candles = '{:,}'.format(candles)

    return [
        Metric('header', None, None, 'Genetic:'),
        Metric('months', months, None, 'Months'),
        Metric('start', start, None, 'Start'),
        Metric('end', end, None, 'End'),
        Metric('candles', candles, None, 'Candles'),
        Metric('days', days, None, 'Days'),
        Metric('population_size', population_size, None, 'Population size'),
        Metric('generations', generations, None, 'Generations'),
        Metric('mutation_rate', mutation_rate, '%', 'Mutation rate'),
        Metric('fitness', fitness, None, 'Fitness'),
        Metric('cores', cores, None, 'Process cores'),
        Metric('opt', opt, None, 'Optimization'),
    ]

def get_genetic_results_metrics(genetic):

    # summarize each generation
    metrics = [ Metric('header', None, None, 'Generations:') ]
    for generation, metric in enumerate(genetic.best_engines):

        # unpack best engines
        path = genetic.parent_path + '/generations' + '/' + str(generation)
        engine = unpack(metric.id, path)

        # percent of population unprofitable
        population_size = genetic.population_size
        unprofitable = genetic.unprofitable_engines[generation]
        profitable_percent = round(((population_size - unprofitable) / population_size) * 100)

        # format
        name = 'generation_' + str(generation)
        title = f'{generation}, {metric.id}'

        # single fitness, unblended
        if len(genetic.fitness.fits) == 1:

            # extract pair
            fit, percent = genetic.fitness.fits[0]

            value = f'\t{fit.pretty}: {metric.value}'
            if fit.unit is not None: value += f' [{fit.unit}]'
            value += f',\tProfitable: {profitable_percent} [%]'

        # multiple fitness targets, blended
        else:

            value = f'\t{display_progress_bar(engine['metrics'])}'
            value += f',\tProfitable: {profitable_percent} [%]'

        # add params
        value += ',\t' + genetic.params[generation].value.one_line

        # align console for large populations
        if 100 > metric.id: value = f'\t' + value

        metrics.append(
            Metric(name, value, None, title))

    return metrics

########################################################################################################################

def print_composite_summary(composite_summary):

    print()
    console = Console()
    padding = Padding(composite_summary, pad = (0, 0, 0, 8))
    console.print(padding)