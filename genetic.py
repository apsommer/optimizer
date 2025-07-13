import shutil
import warnings
from email.generator import Generator
from multiprocessing import Pool

from analysis.Genetic import Genetic
from analysis.WalkForward import WalkForward
from model.Fitness import Fitness
from strategy.LiveParams import LiveParams
from utils import utils
from utils.metrics import *
from utils.utils import *

''' genetic analysis '''
# INPUT ###########################################################

# data, indicators
num_months = 6
isNetwork = False
shouldBuildEmas = True
shouldBuildFractals = True

# genetic params
population_size = 50
generations = 10
mutation_rate = 0.1

# analyzer
opt = LiveParams(
    fastMinutes = [25, 45, 125],
    disableEntryMinutes = [55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
    fastMomentumMinutes = [55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
    fastCrossoverPercent = [0],
    takeProfitPercent = [.25, .3, .35, .4, .45, .5, .55, .6, .65, .7, .75],
    fastAngleFactor = [0],
    slowMinutes = [1555, 2055, 2555, 3055],
    slowAngleFactor = [0, 5, 10, 15, 20, 25],
    coolOffMinutes = [5],
    trendStartHour = [0, 4, 8, 12],
    trendEndHour = [24, 36, 48, 60, 72, 84, 96],
)

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
csv_filename = 'data/' + data_name + '.csv'
parent_path = 'gen/' + data_name
path = parent_path + '/engines'

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
    path = path,
    cores = cores
)

# todo ...

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')
