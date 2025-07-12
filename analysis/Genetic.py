import random

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy


class Genetic:

    def __init__(self, population_size, generations, mutation_rate, data, emas, fractals, opt, path, num_cores):

        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.data = data
        self.emas = emas
        self.fractals = fractals
        self.opt = opt
        self.path = path
        self.num_cores = num_cores

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

    def evaluate(self, generation, core):

        group_size = self.population_size / self.num_cores
        start = group_size * core
        end = start + group_size

        group = self.population[start : end]

        for i, individual in enumerate(group):

            # init strategy and engine
            id = str(generation) + '_' + str(i + group_size * core)
            strategy = LiveStrategy(self.data, self.emas, self.fractals, individual)
            engine = Engine(id, strategy)

            # run and save
            engine.run()
            engine.save(self.path, False)

    def selection(self, population, fitness):

        selected = []

        # unpack engines in population
        # collect their metrics
        # sort on fitness
        # return top slice of N individuals
