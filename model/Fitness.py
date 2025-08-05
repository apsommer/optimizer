import random
from enum import Enum

import numpy as np
import pandas as pd

from model.Metric import Metric
from utils.constants import *

class Fitness:

    def __init__(self, fits):
        self.fits = fits

    def blend(self, engine_metrics):

        # init
        fitness_df = pd.DataFrame(
            index = range(len(engine_metrics)))

        for pair in self.fits:

            # extract tuple
            fit, percent = pair

            # isolate fitness of interest
            fitnesses = []
            for metric in engine_metrics:
                if metric.name == fit.value:
                    fitnesses.append(metric)

            # catch single fitness, no blend required
            if len(self.fits) == 1:
                return fitnesses

            # invert value for negative fitness (drawdown, ...)
            if 0 > fitnesses[0].value:
                for metric in fitnesses:
                    metric.value = -1 / metric.value

            # normalize and scale
            best = max(fitnesses, key = lambda metric: metric.value)
            for metric in fitnesses:
                normalized = metric.value / best.value
                scaled = normalized * percent
                fitness_df.loc[metric.id, fit.value] = scaled

        # blend scaled fitnesses
        values, metrics = fitness_df.sum(axis = 1, skipna = False), []
        for id, value in enumerate(values):
            if np.isnan(value): continue
            metrics.append(
                Metric('blend', value, '%', 'Blend', id = id))

        return metrics

    @property
    def pretty(self):

        pretty = ''
        for pair in self.fits:
            fit, percent = pair
            pretty += '\n\t\t' + fit.pretty + ': ' + str(percent) + ' [%]'

        return pretty

class Fit(Enum):

    # key is name of engine metric
    PROFIT = 'profit'
    PROFIT_FACTOR = 'profit_factor'
    EXPECTANCY = 'expectancy'
    WIN_RATE = 'win_rate'
    AVERAGE_WIN = 'average_win'
    AVERAGE_LOSS = 'average_loss'
    DRAWDOWN = 'drawdown'
    DRAWDOWN_PER_PROFIT = 'drawdown_per_profit'
    CORRELATION = 'correlation'
    NUM_TRADES = 'num_trades'
    NUM_WINS = 'num_wins'

    @property
    def pretty(self):
        match self:
            case Fit.PROFIT: return 'Profit'
            case Fit.PROFIT_FACTOR: return 'Profit Factor'
            case Fit.EXPECTANCY: return 'Expectancy'
            case Fit.WIN_RATE: return 'Win rate'
            case Fit.AVERAGE_WIN: return 'Average win'
            case Fit.AVERAGE_LOSS: return 'Average loss'
            case Fit.DRAWDOWN: return 'Drawdown'
            case Fit.DRAWDOWN_PER_PROFIT: return 'Drawdown per profit'
            case Fit.CORRELATION: return 'Linear correlation'
            case Fit.NUM_TRADES: return 'Number of trades'
            case Fit.NUM_WINS: return 'Number of wins'

    @property
    def color(self):
        match self:
            case Fit.PROFIT: return colors[0]
            case Fit.PROFIT_FACTOR: return colors[1]
            case Fit.EXPECTANCY: return colors[2]
            case Fit.WIN_RATE: return colors[3]
            case Fit.AVERAGE_WIN: return colors[4]
            case Fit.AVERAGE_LOSS: return colors[5]
            case Fit.DRAWDOWN: return colors[6]
            case Fit.DRAWDOWN_PER_PROFIT: return colors[7]
            case Fit.CORRELATION: return colors[8]
            case Fit.NUM_TRADES: return colors[9]
            case Fit.NUM_WINS: return colors[0]

    @property
    def unit(self):
        match self:
            case Fit.PROFIT: return 'USD'
            case Fit.PROFIT_FACTOR: return None
            case Fit.EXPECTANCY: return 'USD'
            case Fit.WIN_RATE: return '%'
            case Fit.AVERAGE_WIN: return 'USD'
            case Fit.AVERAGE_LOSS: return 'USD'
            case Fit.DRAWDOWN: return 'USD'
            case Fit.DRAWDOWN_PER_PROFIT: return 'USD'
            case Fit.CORRELATION: return None
            case Fit.NUM_TRADES: return None
            case Fit.NUM_WINS: return None
