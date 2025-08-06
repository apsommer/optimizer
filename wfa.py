import shutil
import time
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
asset = 'NQ'
num_months = 9
isNetwork = False

# walk forward params
percent = 20
runs = 14 # + 1 added later for final in-sample, use 15 of 16 cores available

# analyzer
opt = LiveParams(
    fastMinutes = [25],
    disableEntryMinutes = [75],
    fastMomentumMinutes = [75], #  np.linspace(55, 135, 9, dtype = int),
    fastCrossoverPercent = [0],
    takeProfitPercent = [.35, .56], # np.around(np.linspace(.25, .75, 6), 2),
    stopLossPercent = [.5], # np.around(np.linspace(.25, .95, 8), 2),
    fastAngleExitFactor= [0],
    slowMinutes = [2405],
    slowAngleFactor = [15],
    coolOffMinutes = [25],
    trendStartHour = [4],
    trendEndHour = [45],
)

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
np.set_printoptions(threshold = 3)
start_time = time.time()

# organize outputs
data_name = asset + '_' + str(num_months) + 'm'
parent_path = 'wfa/' + data_name
analyzer_path = parent_path + '/' + str(percent) + '_' + str(runs)

# get ohlc prices
data = utils.getOhlc(asset, num_months, isNetwork)

# get indicators
getIndicators(data, opt, parent_path)
emas = unpack('emas', parent_path)
fractals = unpack('fractals', parent_path)

# remove any residual analyses
shutil.rmtree(analyzer_path, ignore_errors = True)

# multiprocessing uses all cores
cores = multiprocessing.cpu_count() # 16 available
cores -= 1 # leave 1 for basic computer tasks

# init walk forward
wfa = WalkForward(
    num_months = num_months,
    percent = percent,
    runs = runs,
    data = data,
    emas = emas,
    fractals = fractals,
    opt = opt,
    parent_path = parent_path,
)

# init header metrics
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
fitnesses = [fitness for fitness in Fit]
pool = Pool(
    processes = cores,
    initializer = set_process_name)
pool.map(wfa.build_composite, fitnesses)
pool.close()
pool.join()

# select composite of interest
wfa.analyze()
print_metrics(get_walk_forward_results_metrics(wfa))
wfa.print_fittest_composite()

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')

# plot results
wfa.plot()