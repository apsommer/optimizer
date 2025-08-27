import copy
import random

from analysis.Engine import Engine
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import init_genetic_metrics, get_genetic_results_metrics, print_metrics
from utils.utils import *

class Genetic:

    def __init__(
        self,
        population_size,
        generations,
        mutation_rate,
        fitness,
        data,
        emas,
        fractals,
        opt,
        parent_path,
        cores):

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

        # organize outputs
        self.generations_path = parent_path + '/generations'
        self.analysis_path = parent_path + '/' + format_timestamp(datetime.now(), 'local')
        os.makedirs(self.analysis_path)

        # extract optimization params
        self.fastMinutes = self.opt.fastMinutes
        self.disableEntryMinutes = self.opt.disableEntryMinutes
        self.fastMomentumMinutes = self.opt.fastMomentumMinutes
        self.fastCrossoverPercent = self.opt.fastCrossoverPercent
        self.takeProfitPercent = self.opt.takeProfitPercent
        self.stopLossPercent = self.opt.stopLossPercent
        self.fastAngleEntryFactor = self.opt.fastAngleEntryFactor
        self.fastAngleExitFactor = self.opt.fastAngleExitFactor
        self.slowMinutes = self.opt.slowMinutes
        self.slowAngleFactor = self.opt.slowAngleFactor
        self.coolOffMinutes = self.opt.coolOffMinutes
        self.trendStartHour = self.opt.trendStartHour
        self.trendEndHour = self.opt.trendEndHour

        # track population through generations
        self.population = []
        self.engine_metrics = []
        self.best_engines = []
        self.unprofitable_engines = []
        self.params = []

        # init first population
        self.population = []
        for _ in range(self.population_size):

            individual = LiveParams(
                fastMinutes = random.choice(self.fastMinutes),
                disableEntryMinutes = random.choice(self.disableEntryMinutes),
                fastMomentumMinutes = random.choice(self.fastMomentumMinutes),
                fastCrossoverPercent = random.choice(self.fastCrossoverPercent),
                takeProfitPercent = random.choice(self.takeProfitPercent),
                stopLossPercent = random.choice(self.stopLossPercent),
                fastAngleEntryFactor = random.choice(self.fastAngleEntryFactor),
                fastAngleExitFactor= random.choice(self.fastAngleExitFactor),
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
        path = self.generations_path + '/' + str(generation)

        # segregate population into groups for each core process
        group_size = int(self.population_size / self.cores)
        start = int(group_size * core)
        end = int(start + group_size)
        group = self.population[start : end]

        bar_format = '                  ' + str(generation) + ':    {percentage:3.0f}%|{bar:80}{r_bar}'
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
                engine.run(
                    position = 2,
                    disable = core != 0)
                engine.save(path, False)
                pbar.update()

    def selection(self, generation, tournament_size):

        # organize outputs
        path = self.generations_path + '/' + str(generation)

        # collect engine metrics from last generation
        ids, unprofitable = range(self.population_size), 0
        for id in ids:

            engine_metrics = unpack(id, path)['metrics']

            # filter out engines with loss
            profit = next(metric.value for metric in engine_metrics if metric.name == 'profit')
            if 0 > profit:
                unprofitable += 1
                continue

            self.engine_metrics.extend(engine_metrics)

        # track unprofitable engines
        self.unprofitable_engines.append(unprofitable)
        if len(self.engine_metrics) == 0:
            print(f'{generation}: Entire generation unprofitable.')
            exit()

        # get blended fitnesses
        fitnesses = self.fitness.blend(self.engine_metrics)

        # persist best engine in generation
        best_engine = max(fitnesses, key = lambda metric: metric.value)
        best_params = next(metric for metric in self.engine_metrics
            if metric.name == 'params' and metric.id == best_engine.id)
        self.best_engines.append(best_engine)
        self.params.append(best_params)

        # check for solution convergence
        # applicable only for unblended single fitness, as blending is relative to each generation
        if generation > 2 and len(self.fitness.fits) == 1:
            current_winner = max(self.best_engines, key = lambda metric: metric.value)
            prev_winner = max(self.best_engines[:-1], key = lambda metric: metric.value)
            prev_prev_winner = max(self.best_engines[:-2], key = lambda metric: metric.value)
            if current_winner == prev_winner == prev_prev_winner: return True

        # catch small population in initial generations
        if tournament_size > len(fitnesses):
            tournament_size = len(fitnesses)

        # tournament selection
        selected = []
        for i in range(self.population_size):

            # collect random sample of blended fitness metrics
            group = random.sample(fitnesses, tournament_size)
            winner = max(group, key = lambda metric: metric.value)
            individual = next(metric.value for metric in self.engine_metrics
                if metric.name == 'params' and metric.id == winner.id)

            selected.append(individual)

        # init next generation
        self.population = selected
        self.engine_metrics = []

        # solution has not converged
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

    def analyze(self, generation):

        # catch converged solution
        if generation > len(self.best_engines) - 1: return

        # extract best engine in generation
        metric = self.best_engines[generation]

        # unpack partial results
        path = self.generations_path + '/' + str(generation)
        engine = unpack(metric.id, path)

        # init strategy and engine
        id = 'g' + str(generation) + 'e' + str(metric.id)
        params = next(metric.value for metric in engine['metrics'] if metric.name == 'params')
        strategy = LiveStrategy(self.data, self.emas, self.fractals, params)
        engine = Engine(id, strategy)

        # run and save
        bar_format = '        Plot:           {percentage:3.0f}%|{bar:80}{r_bar}'
        engine.run(
            position = 0,
            disable = generation != 0,
            bar_format = bar_format)

        # make directory
        engine.save(self.analysis_path, True)

    ''' serialize '''
    def save(self):

        # persist results
        self.metrics += get_genetic_results_metrics(self)

        bundle = {
            'metrics': self.metrics,
            'best_engines': self.best_engines
        }

        # save analysis to timestamp directory
        save(
            bundle = bundle,
            filename = 'analysis',
            path = self.analysis_path)

    ####################################################################################################################

    def print_metrics(self):
        print_metrics(self.metrics)

    def plot(self):

        # find engine with highest profit
        winner_profit = 0
        winner_id = ''

        for generation, metric in enumerate(self.best_engines):

            # unpack full results
            id = 'g' + str(generation) + 'e' + str(metric.id)
            engine = unpack(id, self.analysis_path)

            profit = next(metric.value for metric in engine['metrics'] if metric.name == 'profit')
            if profit > winner_profit:
                winner_profit = profit
                winner_id = id

        # unpack winner
        winner = unpack(winner_id, self.analysis_path)
        params = winner['params']
        cash_series = winner['cash_series']
        trades = winner['trades']

        # build engine, but don't run!
        strategy = LiveStrategy(self.data, self.emas, self.fractals, params)
        engine = Engine(winner_id, strategy)
        engine.cash_series = cash_series
        engine.trades = trades
        engine.analyze()

        # display winner
        engine.print_metrics()
        engine.print_trades()
        engine.plot_trades()
        ax = engine.plot_equity(shouldShow = False)

        # overlay each generation
        for generation, metric in enumerate(self.best_engines):

            # unpack full results
            id = 'g' + str(generation) + 'e' + str(metric.id)
            engine = unpack(id, self.analysis_path)

            fplt.plot(
                engine['cash_series'],
                color = colors[generation],
                width = 2,
                ax = ax)

            # format legend
            legend = '<span style="font-size:16pt">' + id + '</span>'
            fplt.legend_text_color = colors[generation]
            fplt.add_legend(legend, ax)

        fplt.show()
