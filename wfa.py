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
num_months = 15
isNetwork = False

# walk forward
percent = 20
runs = 14 # +1 added for final in-sample

# optimization
opt = LiveParams(
    fastMinutes = [20],
    disableEntryMinutes = [110], # np.linspace(55, 255, 201, dtype = int),
    fastMomentumMinutes = [65], # np.linspace(45, 115, 8, dtype = int),
    fastCrossoverPercent = [0], # np.linspace(75, 95, 5),
    takeProfitPercent = [.3, .6], # np.around(np.linspace(.35, 1.05, 8), 2),
    stopLossPercent = [0],
    fastAngleEntryFactor = [0], # np.linspace(0, 100, 101, dtype = int),
    fastAngleExitFactor = [2155], # np.linspace(1000, 3000, 401, dtype = int),
    slowMinutes = [2555],
    slowAngleFactor = [0], # np.linspace(3, 18, 6, dtype = int),
    coolOffMinutes = [5], # np.linspace(0, 25, 26, dtype = int),
    trendStartHour = [4], # np.linspace(0, 12, 13, dtype = int),
    trendEndHour = [72], # np.linspace(12, 212, 201, dtype = int),
)

###################################################################

# clean console
os.system('clear')
warnings.filterwarnings('ignore')
np.set_printoptions(threshold = 3)
start_time = time.time()

# organize outputs
data_name = asset + '_' + str(num_months) + 'm'
data_path = 'data/' + data_name
parent_path = 'wfa/' + data_name
analyzer_path = parent_path + '/' + str(percent) + '_' + str(runs)

# init data and indicators
data = getOhlc(asset, num_months, isNetwork)
emas, fractals = getIndicators(data, opt, data_path)

# remove residual analyses
shutil.rmtree(analyzer_path, ignore_errors = True)

# multiprocessing uses all cores, 16 available, leave 1 for basic tasks
cores = multiprocessing.cpu_count() - 1

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
pool = Pool(cores)
pool.map(wfa.in_sample, range(runs + 1)) # add 1 for last IS (prediction)
pool.close()
pool.join()

# run out-of-sample for each fitness
pool = Pool(cores)
pool.map(wfa.out_of_sample, range(runs))
pool.close()
pool.join()

# build composite engines
fits = [fit for fit in Fit]
pool = Pool(cores)
pool.map(wfa.build_composite, fits)
pool.close()
pool.join()

# select composite of interest
wfa.analyze()
print_metrics(get_walk_forward_results_metrics(wfa))
wfa.print_composite_summary()
wfa.print_last_analyzer()

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')

# plot results
wfa.plot()