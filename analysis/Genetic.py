import random

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy


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

        group_size = self.population_size / self.cores
        start = group_size * core
        end = start + group_size

        group = self.population[start : end]

        for i, individual in enumerate(group):

            # init strategy and engine
            id = i + group_size * core
            strategy = LiveStrategy(self.data, self.emas, self.fractals, individual)
            engine = Engine(id, strategy)

            # run and save
            engine.run()
            self.engine_metrics.append(engine.metrics)

        print(self.engine_metrics)

    def selection(self, fitness, tournament_size = 3):

        selected = []
        fitnesses = []

        # isolate fitness of interest
        for metric in self.engine_metrics:
            if metric.name == fitness.value:
                fitnesses.append(metric)

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

    def crossover(self):

        next_generation = []

        # loop population in parent pairs
        for i in range(0, len(self.population), 2):

            # init family
            mother = self.population[i]
            father = self.population[i + 1]
            son, daughter = mother, father

            # random float between 0-1
            alpha = random.random()
            for chromosome, mother_gene in vars(mother).items():

                # get father's gene
                father_gene = father.chromosome

                # blend (crossover) parents to construct children
                son.chromosome = (alpha * mother_gene) + (1 - alpha) * father_gene
                daughter.chromosome = (alpha * father_gene) + (1 - alpha) * mother_gene

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


