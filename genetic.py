import shutil
import time
import warnings
from functools import partial
from multiprocessing import Pool

from analysis.Genetic import Genetic
from model.Fitness import Fit, Fitness
from strategy.LiveParams import LiveParams
from utils import utils
from utils.metrics import print_metrics, get_genetic_results_metrics
from utils.utils import *

''' genetic analysis '''
# INPUT ###########################################################

# data, indicators
num_months = 3
isNetwork = False

# genetic params
population_size = 15
generations = 2
mutation_rate = 0.05

# todo encapsulate to class, extract commons for wfa use
fitness = Fitness(
    fits= [
        # (Fit.PROFIT, 50),
        (Fit.NUM_WINS, 50),
        (Fit.CORRELATION, 50),
    ])

# optimization
opt = LiveParams(
    fastMinutes = [20],
    disableEntryMinutes = np.linspace(55, 155, 101, dtype = int),
    fastMomentumMinutes = np.linspace(55, 155, 101, dtype = int),
    fastCrossoverPercent = [0], # np.linspace(70,100, 31, dtype = int),
    takeProfitPercent = np.around(np.linspace(.1, .75, 66), 2),
    stopLossPercent = [1],
    fastAngleFactor = [0],
    slowMinutes = [2255], # np.linspace(2005, 3005, 11, dtype = int),
    slowAngleFactor = np.linspace(0, 25, 26, dtype = int),
    coolOffMinutes = [5],
    trendStartHour = np.linspace(0, 24, 25, dtype = int),
    trendEndHour = np.linspace(24, 124, 101, dtype = int),
)

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
np.set_printoptions(threshold = 3)
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
csv_filename = 'data/' + data_name + '.csv'
parent_path = 'genetic/' + data_name
path = parent_path + '/generations'

# get ohlc prices
data = utils.getOhlc(num_months, isNetwork)

# get indicators
check_indicators(data, opt, parent_path)
emas = unpack('emas', parent_path)
fractals = unpack('fractals', parent_path)

# remove residual analyses
shutil.rmtree(path, ignore_errors = True)

# multiprocessing uses all cores
cores = multiprocessing.cpu_count() # 16 available
cores -= 1 # leave 1 for basic computer tasks

# init genetic analysis
genetic = Genetic(
    population_size = population_size,
    generations = generations,
    mutation_rate = mutation_rate,
    fitness= fitness,
    data = data,
    emas = emas,
    fractals = fractals,
    opt = opt,
    parent_path = parent_path,
    cores = cores)

# init header metrics
print_metrics(genetic.metrics)

# execute genetic algorithm
bar_format = '        Generations:    {percentage:3.0f}%|{bar:100}{r_bar}'
with tqdm(
    position = 0,
    leave = False,
    total = generations,
    colour = purple,
    bar_format = bar_format) as pbar:

    for generation in range(generations):

        # split population between process cores and evaluate
        pool = Pool(
            processes = cores,
            initializer = set_process_name)
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
            print('\n\n\tSolution converged.')
            break

        genetic.crossover()
        genetic.mutation()
        genetic.clean()

        # add comment progress bar
        best = genetic.best_engines[generation]
        pbar.set_postfix_str(f'{round(best.value)}%')
        pbar.update()

# run and save best engines
pool = Pool(
    processes = cores,
    initializer = set_process_name)
pool.map(
    func = genetic.analyze,
    iterable = range(generations))
pool.close()
pool.join()

genetic.save()

# display results
genetic.print_metrics()
genetic.plot()

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')
