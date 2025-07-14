import random
import copy

import numpy as np
from tqdm import tqdm

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.constants import *
from utils.utils import *

class Genetic:

    def __init__(self, population_size, generations, mutation_rate, data, emas, fractals, opt, path, cores):

        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.data = data
        self.emas = emas
        self.fractals = fractals
        self.opt = opt
        self.path = path
        self.cores = cores

        # extract optimization params
        self.fastMinutes = self.opt.fastMinutes
        self.disableEntryMinutes = self.opt.disableEntryMinutes
        self.fastMomentumMinutes = self.opt.fastMomentumMinutes
        self.fastCrossoverPercent = self.opt.fastCrossoverPercent
        self.takeProfitPercent = self.opt.takeProfitPercent
        self.fastAngleFactor = self.opt.fastAngleFactor
        self.slowMinutes = self.opt.slowMinutes
        self.slowAngleFactor = self.opt.slowAngleFactor
        self.coolOffMinutes = self.opt.coolOffMinutes
        self.trendStartHour = self.opt.trendStartHour
        self.trendEndHour = self.opt.trendEndHour

        # track population through generations
        self.population = []
        self.engine_metrics = []

        # init first population
        self.population = []
        for _ in range(self.population_size):

            individual = LiveParams(
                fastMinutes = random.choice(self.fastMinutes),
                disableEntryMinutes = random.choice(self.disableEntryMinutes),
                fastMomentumMinutes = random.choice(self.fastMomentumMinutes),
                fastCrossoverPercent = random.choice(self.fastCrossoverPercent),
                takeProfitPercent = random.choice(self.takeProfitPercent),
                fastAngleFactor = random.choice(self.fastAngleFactor),
                slowMinutes = random.choice(self.slowMinutes),
                slowAngleFactor = random.choice(self.slowAngleFactor),
                coolOffMinutes = random.choice(self.coolOffMinutes),
                trendStartHour = random.choice(self.trendStartHour),
                trendEndHour = random.choice(self.trendEndHour),
            )

            self.population.append(individual)

    def evaluate(self, core):

        # segregate population into groups for each core process todo int or round? might miss 1?
        group_size = int(self.population_size / self.cores)
        start = int(group_size * core)
        end = int(start + group_size)
        group = self.population[start : end]

        with tqdm(
            disable = core != 0, # show only 1 core
            total = group_size,
            colour = blue,
            bar_format = '        Evaluate:       {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            for i, individual in enumerate(group):

                # init strategy and engine
                id = i + group_size * core
                strategy = LiveStrategy(self.data, self.emas, self.fractals, individual)
                engine = Engine(id, strategy)

                # run and save
                engine.run()
                engine.save(self.path, False)

                pbar.update()

    def selection(self, fitness, tournament_size = 3):

        selected = []
        fitnesses = []

        # unpack last generation
        ids = np.arange(0, self.population_size, 1)
        for id in ids:
            engine_metrics = unpack(id, self.path)['metrics']
            self.engine_metrics.extend(engine_metrics)

        # isolate fitness of interest
        for metric in self.engine_metrics:
            if metric.name == fitness.value:
                fitnesses.append(metric)

        # todo consider roulette wheel, rank-based, ...
        # tournament selection
        for i in range(len(self.population)):

            # random select group of individuals
            group = random.sample(fitnesses, tournament_size)
            winner = max(group, key = lambda metric: metric.value)

            individual = next(metric.value for metric in self.engine_metrics
                if metric.name == 'params' and metric.id == winner.id)

            selected.append(individual)

        # init next generation
        self.population = selected

    def crossover(self):

        next_generation = []

        # loop population in parent pairs
        for i in range(0, len(self.population), 2):

            # catch odd numbered population
            if i + 1 == len(self.population):
                next_generation.append(self.population[i])
                continue

            # init family
            mother = self.population[i]
            father = self.population[i + 1]
            son = copy.copy(mother)
            daughter = copy.copy(father)

            for chromosome, mother_gene in vars(mother).items():

                # random float between 0-1
                alpha = random.random()

                # get father's gene
                father_gene = getattr(father, chromosome)

                # blend (crossover) parents to construct children
                setattr(son, chromosome, (alpha * mother_gene) + (1 - alpha) * father_gene)
                setattr(daughter, chromosome, (alpha * father_gene) + (1 - alpha) * mother_gene)

            next_generation.append(son)
            next_generation.append(daughter)

        self.population = next_generation

    def mutation(self):

        for individual in self.population:

            for chromosome, gene in vars(individual).items():

                alpha = random.random()
                if alpha < self.mutation_rate:

                    mutated_gene = random.randint(min(self.opt.chromosome), max(self.opt.chromosome))
                    individual.chromosome = mutated_gene


