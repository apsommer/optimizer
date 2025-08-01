import shutil
import time
import warnings
from functools import partial
from multiprocessing import Pool

from analysis.Genetic import Genetic
from model.Fitness import Fit, Fitness
from strategy.LiveParams import LiveParams
from utils.metrics import print_metrics, get_genetic_results_metrics, get_pf_trades
from utils.utils import *

''' genetic analysis '''
# INPUT ###########################################################

# data, indicators
asset = 'ES'
num_months = 3 # trump elected 051124

# genetic params
population_size = 15
generations = 2
mutation_rate = 0.05

fitness = Fitness(
    fits = [
        (Fit.DRAWDOWN_PER_PROFIT, 100),
        # (Fit.NUM_WINS, 30),
    ])

# optimization
opt = LiveParams(
    fastMinutes = [20],
    disableEntryMinutes = np.linspace(55, 255, 201, dtype = int),
    fastMomentumMinutes = np.linspace(55, 155, 101, dtype = int),
    fastCrossoverPercent = [0], # np.linspace(70, 100, 31, dtype = int),
    takeProfitPercent = np.around(np.linspace(.3, 1, 71), 2),
    stopLossPercent = [0], # np.around(np.linspace(.25, 1, 76), 2),
    fastAngleEntryFactor = np.linspace(0, 1000, 1001, dtype = int),
    fastAngleExitFactor= np.linspace(1250, 5250, 4001, dtype = int),
    slowMinutes = [2555], # np.linspace(2005, 3005, 5, dtype = int),
    slowAngleFactor = np.linspace(0, 50, 51, dtype = int),
    coolOffMinutes = [5], # np.linspace(0, 25, 26, dtype = int),
    trendStartHour = np.linspace(0, 12, 13, dtype = int),
    trendEndHour = np.linspace(12, 112, 101, dtype = int),
)

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
np.set_printoptions(threshold = 3)
start_time = time.time()

# organize outputs
data_name = asset + '_' + str(num_months) + 'm'
data_path = 'data/' + data_name
parent_path = 'genetic/' + data_name
path = parent_path + '/generations'

# init data and indicators
data = getOhlc(asset, num_months)
emas, fractals = getIndicators(data, opt, data_path)

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
bar_format = '        Generations:    {percentage:3.0f}%|{bar:80}{r_bar}'
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
            tournament_size = 5)

        if isSolutionConverged:
            print(f'\n\n\t{generation}: Solution converged.')
            break

        genetic.crossover()
        genetic.mutation()
        genetic.clean()

        # add comment to progress bar
        best_metric = genetic.best_engines[generation]
        best_engine = unpack(best_metric.id, path + '/' + str(generation))
        pbar.set_postfix_str(get_pf_trades(best_engine['metrics']))
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
print_metrics(get_genetic_results_metrics(genetic))
genetic.plot()

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')
