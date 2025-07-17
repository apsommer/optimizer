import copy
import random

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import init_genetic_metrics, get_genetic_results_metrics
from utils.utils import *

class Genetic:

    def __init__(self, population_size, generations, mutation_rate, fitness, data, emas, fractals, opt, parent_path, cores):

        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.data = data
        self.fitness = fitness
        self.emas = emas
        self.fractals = fractals
        self.opt = opt
        self.parent_path = parent_path
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
        self.best_engines = []
        self.winner = None

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

        # init metrics
        self.metrics = init_genetic_metrics(self)

    def evaluate(self, core, generation):

        # organize outputs
        path = self.parent_path + '/' + str(generation)

        # segregate population into groups for each core process
        group_size = int(self.population_size / self.cores)
        start = int(group_size * core)
        end = int(start + group_size)
        group = self.population[start : end]

        bar_format = '                  ' + str(generation) + ':    {percentage:3.0f}%|{bar:100}{r_bar}'
        with tqdm(
            disable = core != 0, # show only 1 core
            position = 1,
            leave = False,
            total = group_size,
            colour = blue,
            bar_format = bar_format) as pbar:

            for i, individual in enumerate(group):

                # init strategy and engine
                id = i + group_size * core
                strategy = LiveStrategy(self.data, self.emas, self.fractals, individual)
                engine = Engine(id, strategy)

                # run and save
                engine.run()
                engine.save(path, False)

                pbar.update()

    def selection(self, generation, tournament_size = 3):

        # organize outputs
        path = self.parent_path + '/' + str(generation)

        selected = []
        fitnesses = []

        # unpack last generation
        ids = range(self.population_size)
        for id in ids:
            engine_metrics = unpack(id, path)['metrics']
            self.engine_metrics.extend(engine_metrics)

        # isolate fitness of interest
        for metric in self.engine_metrics:
            if metric.name == self.fitness.value:
                fitnesses.append(metric)

        # sort by value
        fitnesses = sorted(
            fitnesses,
            key = lambda it: it.value,
            reverse = True)

        # persist best engine in generation
        self.best_engines.append(fitnesses[0])

        # check if solution has converged
        if generation > 2 and self.best_engines[-3] == self.best_engines[-2] == self.best_engines[-1]:
            return True

        # todo consider roulette wheel, rank-based, ...
        # tournament selection
        for i in range(self.population_size):

            # random select group of individuals
            group = random.sample(fitnesses, tournament_size)
            winner = max(group, key = lambda metric: metric.value)

            individual = next(metric.value for metric in self.engine_metrics
                if metric.name == 'params' and metric.id == winner.id)

            selected.append(individual)

        # init next generation
        self.population = selected
        self.engine_metrics = []

        # solution has not yet converged
        return False

    def crossover(self):

        next_generation = []

        # loop population in parent pairs
        for i in range(0, self.population_size, 2):

            # catch odd numbered population
            if i + 1 == self.population_size:
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
            for chromosome in vars(individual).keys():

                # random float between 0-1
                alpha = random.random()
                if self.mutation_rate > alpha:

                    # select gene at random
                    available_genes = getattr(self, chromosome)
                    mutated_gene = random.choice(available_genes)

                    # mutate gene
                    setattr(individual, chromosome, mutated_gene)

    def clean(self):

        for individual in self.population:
            for chromosome, individual_gene in vars(individual).items():

                # align gene to closest available
                available_genes = getattr(self, chromosome)
                closest_gene = min(available_genes, key = lambda gene: abs(gene - individual_gene))
                setattr(individual, chromosome, closest_gene)

    def analyze(self):

        # isolate solution
        winner_metric = max(self.best_engines, key = lambda it: it.value)
        winner_generation = self.best_engines.index(winner_metric)

        # run and save best engine in each generation
        for generation, metric in enumerate(self.best_engines):

            # unpack partial results
            path = self.parent_path + '/' + str(generation)
            engine = unpack(metric.id, path)

            # init strategy and engine
            id = 'g' + str(generation) + 'e' + str(metric.id)
            params = next(metric.value for metric in engine['metrics'] if metric.name == 'params')
            strategy = LiveStrategy(self.data, self.emas, self.fractals, params)
            engine = Engine(id, strategy)

            # run and save
            engine.run()
            engine.save(self.parent_path, True)

            # persist solution
            if generation == winner_generation:
                self.winner = copy.copy(engine)

        self.metrics += get_genetic_results_metrics(self)

    ####################################################################################################################

    def plot(self):

        ax = init_plot(
            window = 1,
            title = 'Equity')

        # plot equity of best engines
        for generation, metric in enumerate(self.best_engines):

            # unpack full results
            id = 'g' + str(generation) + 'e' + str(metric.id)
            engine = unpack(id, self.parent_path)

            fplt.plot(
                engine['cash_series'],
                color = get_ribbon_color(generation),
                width = generation,
                legend = str(generation),
                ax = ax)

        # display winner
        self.winner.print_metrics()
        self.winner.print_trades()
        self.winner.plot_trades()

        fplt.show()
