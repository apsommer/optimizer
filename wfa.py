import shutil
import warnings
from multiprocessing import Pool

from analysis.WalkForward import WalkForward
from model.Fitness import Fit
from strategy.LiveParams import LiveParams
from utils import utils
from utils.metrics import *
from utils.utils import *

''' walk-forward analysis '''
# INPUT ###########################################################

# data, indicators
num_months = 20
isNetwork = False
shouldBuildEmas = False
shouldBuildFractals = False

# walk forward
percent = 20
runs = 14 # + 1 added later for final in-sample, use 15 of 16 cores available

# analyzer
opt = LiveParams(
    fastMinutes = [25],
    disableEntryMinutes = [95, 105, 125],
    fastMomentumMinutes = [65, 75, 85, 95, 105, 115, 125],
    fastCrossoverPercent = [0],
    takeProfitPercent = [.35, .45, .55],
    fastAngleFactor = [0],
    slowMinutes = [2555],
    slowAngleFactor = [15, 20],
    coolOffMinutes = [5],
    trendStartHour = [0],
    trendEndHour = [48, 60],
)

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
parent_path = 'wfa/' + data_name
path = parent_path + '/' + str(percent) + '_' + str(runs)

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

# init walk forward
wfa = WalkForward(
    num_months = num_months,
    percent = percent,
    runs = runs,
    data = data,
    emas = emas,
    fractals = fractals,
    opt = opt,
    path = path)

# multiprocessing uses all cores
cores = multiprocessing.cpu_count() # 16 available
cores -= 1 # leave 1 for basic computer tasks
fitnesses = [fitness for fitness in Fit]

# print header metrics
print_metrics(wfa.metrics)

# run in-sample sweep
pool = Pool(
    processes = cores,
    initializer = set_process_name)
pool.map(wfa.in_sample, range(runs + 1)) # add 1 for last IS (prediction)
pool.close()
pool.join()

# run out-of-sample for each fitness
pool = Pool(
    processes = cores,
    initializer = set_process_name)
pool.map(wfa.out_of_sample, range(runs))
pool.close()
pool.join()

# build composite engines
pool = Pool(
    processes = cores,
    initializer = set_process_name)
pool.map(wfa.build_composite, fitnesses)
pool.close()
pool.join()

# select composite of interest
wfa.analyze()
print_metrics(get_walk_forward_results_metrics(wfa))
wfa.print_params_of_fittest_composite()

# print last in-sample analyzer
IS_path = wfa.path + '/' + str(runs)
analyzer_metrics = unpack('analyzer', IS_path)['metrics']
print_metrics(analyzer_metrics)

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')

# plot results
wfa.plot()