import shutil
import warnings
from functools import partial
from multiprocessing import Pool

from analysis.Genetic import Genetic
from model.Fitness import Fitness
from strategy.LiveParams import LiveParams
from utils import utils
from utils.metrics import print_metrics, init_genetic_metrics
from utils.utils import *

''' genetic analysis '''
# INPUT ###########################################################

# data, indicators
num_months = 3
isNetwork = False
shouldBuildEmas = False
shouldBuildFractals = False

# genetic params
population_size = 150
generations = 10
mutation_rate = 0.05
fitness = Fitness.PROFIT

# analyzer
opt = LiveParams(
    fastMinutes = [25],
    disableEntryMinutes = np.linspace(55, 155, 101),
    fastMomentumMinutes = np.linspace(55, 155, 101),
    fastCrossoverPercent = np.linspace(70,100, 31),
    takeProfitPercent = np.linspace(.25, .75, 51),
    fastAngleFactor = [0],
    slowMinutes = [1855, 1955, 2055, 2155, 2355, 2455, 2555],
    slowAngleFactor = np.linspace(0, 25, 26),
    coolOffMinutes = np.linspace(0, 60, 61),
    trendStartHour = np.linspace(0, 24, 25),
    trendEndHour = np.linspace(24, 124, 101))

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

# build indicators
if shouldBuildEmas or shouldBuildFractals:
    print(f'Indicators:')
if shouldBuildEmas: build_emas(data, parent_path)
if shouldBuildFractals: build_fractals(data, parent_path)
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

    #
    pool = Pool(
        processes = cores,
        initializer = set_process_name)
    pool.map(
        func = partial(
            genetic.evaluate, generation = generation),
        iterable = range(cores))
    pool.close()
    pool.join()

    # todo cascade from .evaluation and remove extra args
    isSolutionConverged = genetic.selection(fitness, generation)
    if isSolutionConverged:
        print('\tSolution converged.')
        break

    genetic.crossover()
    genetic.mutation()
    genetic.clean()

# todo summary metrics
for generation, metric in enumerate(genetic.best_engines):
    print(f'\t{generation}: [{metric.id}], {fitness.pretty}: {round(metric.value)}')

# display results
winner = unpack(
    id = genetic.best_engines[-1].id,
    path = path + '/' + str(generations - 1))
print_metrics(winner['metrics'])

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')
