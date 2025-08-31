import shutil
import time
import warnings
from multiprocessing import Pool

from analysis.WalkForward import WalkForward
from model.Fitness import Fit, Fitness
from strategy.LiveParams import LiveParams
from utils import utils
from utils.metrics import *
from utils.utils import *

''' walk-forward analysis '''
# INPUT ###########################################################

# data, indicators
asset = 'ES'
num_months = 20
isNetwork = False

# walk forward
percent = 25
runs = 9 # +1 added for final in-sample
fitness = Fitness(
    fits = [
        (Fit.WIN_RATE, 25),
        (Fit.CORRELATION, 75),
    ])

# optimization
opt = LiveParams(
    fastMinutes = [25],
    disableEntryMinutes = [105], # np.linspace(55, 255, 201, dtype = int),
    fastMomentumMinutes = np.linspace(95, 135, 9, dtype = int),
    fastCrossoverPercent = [0], # np.linspace(75, 95, 5),
    takeProfitPercent = np.around(np.linspace(.25, .65, 9), 2),
    stopLossPercent = [0] , # np.around(np.linspace(.45, .95, 11), 2),
    fastAngleEntryFactor = np.linspace(10, 50, 9, dtype = int),
    fastAngleExitFactor = [2050], # np.linspace(1000, 3000, 401, dtype = int),
    slowMinutes = [2150],
    slowAngleFactor = [25], # np.linspace(10, 50, 9, dtype = int),
    coolOffMinutes = [10], # np.linspace(0, 25, 26, dtype = int),
    trendStartHour = [6], # np.linspace(0, 12, 13, dtype = int),
    trendEndHour = [142], # np.linspace(12, 212, 201, dtype = int),
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
    fitness = fitness,
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
print_composite_summary(wfa.composite_summary)
wfa.print_last_analyzer()

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')

# plot results
wfa.plot()