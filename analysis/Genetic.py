import random

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.utils import unpack


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

        group_size = self.population_size / self.cores
        start = group_size * core
        end = start + group_size

        group = self.population[start : end]

        path = self.path + '/' + str(generation)

        for i, individual in enumerate(group):

            # init strategy and engine
            id = i + group_size * core
            strategy = LiveStrategy(self.data, self.emas, self.fractals, individual)
            engine = Engine(id, strategy)

            # run and save
            engine.run()
            engine.save(path, False)

    def selection(self, generation, fitness, tournament_size = 3):

        selected = []
        fitnesses = []
        path = self.path + '/' + str(generation)

        # unpack engines in generation
        for i in range(len(self.population)):

            engine_metrics = unpack(i, path)['metrics']
            fitness_metric = next(metric for metric in engine_metrics if metric.name == fitness.value)
            fitnesses.append(fitness_metric)

        # # sort on fitness
        # fitnesses = sorted(
        #     fitnesses,
        #     key = lambda it: it.value,
        #     reverse = True)

        # todo consider roulette wheel, rank-based, ...
        # tournament selection
        for i in range(len(self.population)):
            group = random.sample(fitnesses, tournament_size)
            winner = max(group, key = lambda metric: metric.value)
            selected.append(winner)

        # init next generation
        self.population = selected

    def crossover(self, mother, father):

        # init children
        son = mother
        daughter = mother

        for chromosome, mother_gene in vars(mother).items():

            # get father's gene
            father_gene = father.chromosome

            # random 0 or 1
            a = random.randint(0, 1)
            b = random.randint(0, 1)

            if a == 0: son.chromosome = mother_gene
            else: son.chromosome = father_gene

            if b == 0: daughter.chromosome = mother_gene
            else: daughter.chromosome = father_gene

        return son, daughter


