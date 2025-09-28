import shutil
import time
import warnings
from functools import partial
from multiprocessing import Pool

from analysis.Genetic import Genetic
from model.Fitness import Fit, Fitness
from strategy.LiveParams import LiveParams
from utils.metrics import print_metrics, get_genetic_results_metrics, display_progress_bar
from utils.utils import *

########################################################################################################################

# data, indicators
asset = 'NKD'
num_months = 15
isNetwork = False

# genetic
population_size = 100
generations = 7
mutation_rate = 0.05
fitness = Fitness(
    fits = [
        (Fit.PROFIT_FACTOR, 60),
        (Fit.DRAWDOWN_PER_PROFIT, 20),
        (Fit.NUM_WINS, 20),
        # (Fit.CORRELATION, 10),
    ])

# multiprocessing uses all cores, 16 available, leave 1 for basic tasks
cores = 10 # multiprocessing.cpu_count() - 1

# optimization
opt = LiveParams(
    fastMinutes = np.linspace(25, 155, 14, dtype = int), # [25],
    disableEntryMinutes = np.linspace(60, 240, 181, dtype = int),
    fastMomentumMinutes = np.linspace(55, 155, 101, dtype = int),
    fastCrossoverPercent = [0], # np.linspace(70, 100, 31),
    takeProfitPercent = np.around(np.linspace(0.25, 1.25, 101), 2),
    stopLossPercent = [0], # np.around(np.linspace(0.2, 1.2, 101), 2),
    fastAngleEntryFactor = np.linspace(0, 50,  51, dtype = int),
    fastAngleExitFactor = np.linspace(1000, 4000, 3001, dtype = int),
    slowMinutes = np.linspace(2055, 3555, 7, dtype = int),
    slowAngleFactor = np.linspace(0, 50, 51, dtype = int),
    coolOffMinutes = np.linspace(0, 25, 26, dtype = int),
    trendStartHour = np.linspace(0, 12, 13, dtype = int),
    trendEndHour = np.linspace(12, 180, 169, dtype = int),
)

########################################################################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# organize outputs
data_name = asset + '_' + str(num_months) + 'm'
data_path = 'data/' + data_name
parent_path = 'genetic/' + data_name
path = parent_path + '/generations'

# init data and indicators
data = getOhlc(asset, num_months, isNetwork)
emas, fractals = getIndicators(data, opt, data_path)

# remove residual analyses
shutil.rmtree(path, ignore_errors = True)

# init genetic analysis
genetic = Genetic(
    population_size = population_size,
    generations = generations,
    mutation_rate = mutation_rate,
    fitness = fitness,
    data = data,
    emas = emas,
    fractals = fractals,
    opt = opt,
    parent_path = parent_path,
    cores = cores)

# init header metrics
print_metrics(genetic.metrics)

# execute genetic algorithm
bar_format = '        Generations:    {percentage:3.0f}%|{bar:80}{r_bar}'
with tqdm(
    position = 0,
    leave = False,
    total = generations,
    colour = purple,
    bar_format = bar_format) as pbar:

    for generation in range(generations):

        # split population between process cores and evaluate
        pool = Pool(cores)
        pool.map(
            func = partial(genetic.evaluate, generation = generation),
            iterable = range(cores))
        pool.close()
        pool.join()

        # check for convergence
        isSolutionConverged = genetic.selection(
            generation = generation,
            tournament_size = 3)

        if isSolutionConverged:
            print(f'\n\n\t{generation}: Solution converged.')
            break

        genetic.crossover()
        genetic.mutation()
        genetic.clean()

        # add comment to progress bar
        best_metric = genetic.best_engines[generation]
        best_engine = unpack(best_metric.id, path + '/' + str(generation))
        pbar.set_postfix_str(display_progress_bar(best_engine['metrics']))
        pbar.update()

# run and save best engines
pool = Pool(cores)
pool.map(
    func = genetic.analyze,
    iterable = range(generations))
pool.close()
pool.join()
genetic.save()

# display results
print_metrics(get_genetic_results_metrics(genetic))
genetic.plot()

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')
