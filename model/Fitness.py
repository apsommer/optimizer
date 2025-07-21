import random
from enum import Enum

import numpy as np
import pandas as pd

from model.Metric import Metric
from utils.constants import *

class BlendedFitness:

    def __init__(self, tuples):
        self.tuples = tuples

    def blend(self, engine_metrics):

        # init
        fitness_df = pd.DataFrame(
            index = range(len(engine_metrics)))

        for pair in self.tuples:

            # extract tuple
            fitness, percent = pair

            # isolate fitness of interest
            fitnesses = []
            for metric in engine_metrics:
                if metric.name == fitness.value:
                    fitnesses.append(metric)

            # normalize and scale
            best = max(fitnesses, key = lambda metric: metric.value)
            for metric in fitnesses:
                normalized = metric.value / best.value
                scaled = normalized * percent
                fitness_df.loc[metric.id, fitness.value] = scaled

        # blend scaled fitnesses
        blended_values, blended_metrics = fitness_df.sum(axis = 1, skipna = False), []
        for id, blended_value in enumerate(blended_values):
            if np.isnan(blended_value): continue
            blended_metrics.append(
                Metric('blended_fitness', blended_value, '%', 'Fitness blend', id = id))

        return blended_metrics

class Fitness(Enum):

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

    @property
    def pretty(self):
        match self:
            case Fitness.PROFIT: return 'Profit'
            case Fitness.PROFIT_FACTOR: return 'Profit Factor'
            case Fitness.EXPECTANCY: return 'Expectancy'
            case Fitness.WIN_RATE: return 'Win rate'
            case Fitness.AVERAGE_WIN: return 'Average win'
            case Fitness.AVERAGE_LOSS: return 'Average loss'
            case Fitness.DRAWDOWN: return 'Drawdown'
            case Fitness.DRAWDOWN_PER_PROFIT: return 'Drawdown per profit'
            case Fitness.CORRELATION: return 'Linear correlation'
            case Fitness.NUM_TRADES: return 'Number of trades'

    @property
    def color(self):
        i = random.randint(0, len(colors) - 1)
        return colors[i]