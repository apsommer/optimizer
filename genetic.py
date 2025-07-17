import shutil
import warnings
from functools import partial
from multiprocessing import Pool

from analysis.Genetic import Genetic
from model.Fitness import Fitness
from strategy.LiveParams import LiveParams
from utils import utils
from utils.metrics import print_metrics, get_genetic_results_metrics
from utils.utils import *

''' genetic analysis '''
# INPUT ###########################################################

# data, indicators
num_months = 12
isNetwork = False

# genetic params
population_size = 150
generations = 7
mutation_rate = 0.05
fitness = Fitness.DRAWDOWN_PER_PROFIT

# analyzer
opt = LiveParams(
    fastMinutes = [25],
    disableEntryMinutes = np.linspace(55, 155, 101, dtype = int),
    fastMomentumMinutes = np.linspace(55, 155, 101, dtype = int),
    fastCrossoverPercent = np.linspace(70,100, 31, dtype = int),
    takeProfitPercent = np.around(np.linspace(.25, .75, 51), 2),
    fastAngleFactor = [0],
    slowMinutes = np.linspace(1555, 3555, 9, dtype = int),
    slowAngleFactor = np.linspace(0, 25, 26, dtype = int),
    coolOffMinutes = np.linspace(0, 60, 61, dtype = int),
    trendStartHour = np.linspace(0, 24, 25, dtype = int),
    trendEndHour = np.linspace(24, 124, 101, dtype = int),
)

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
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

# remove any residual analyses
shutil.rmtree(path, ignore_errors=True)

# multiprocessing uses all cores
cores = multiprocessing.cpu_count() # 16 available
cores -= 1 # leave 1 for basic computer tasks

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
    parent_path = path,
    cores = cores)

# init header metrics
print_metrics(genetic.metrics)

# execute genetic algorithm
bar_format = '        Generations:    {percentage:3.0f}%|{bar:100}{r_bar}'
for generation in tqdm(
    iterable = range(generations),
    position = 0,
    colour = green,
    bar_format = bar_format):

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
        print('\tSolution converged.')
        break

    genetic.crossover()
    genetic.mutation()
    genetic.clean()

genetic.analyze()
print_metrics(get_genetic_results_metrics(genetic))
genetic.plot()

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')
