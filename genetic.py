import shutil
import warnings
from functools import partial
from multiprocessing import Pool

from analysis.Genetic import Genetic
from model.Fitness import Fitness
from strategy.LiveParams import LiveParams
from utils import utils
from utils.metrics import print_metrics
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
generations = 5
mutation_rate = 0.05
fitness = Fitness.PROFIT

# analyzer
opt = LiveParams(
    fastMinutes = [25, 45, 65],
    disableEntryMinutes = np.linspace(55, 155, 101),
    fastMomentumMinutes = np.linspace(55, 155, 101),
    fastCrossoverPercent = [0],
    takeProfitPercent = np.linspace(.25, .75, 51),
    fastAngleFactor = [0],
    slowMinutes = [1555, 2055, 2555, 3055],
    slowAngleFactor = np.linspace(0, 50, 51),
    coolOffMinutes = [5],
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

# todo init some header metrics

for generation in range(generations):

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
    genetic.selection(fitness, generation)
    genetic.crossover()
    genetic.mutation()
    genetic.clean()

print()
print_metrics(genetic.best_engines)

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')
