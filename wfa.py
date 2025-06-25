import multiprocessing
import os
import random
import re
import shutil
import time
import warnings

import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, Process

from analysis.Engine import Engine
from analysis.WalkForward import WalkForward

from model.Fitness import Fitness
from strategy.LiveStrategy import LiveStrategy
from utils import utils
from utils.utils import *
from utils.metrics import *

''' walk-forward analysis '''
# INPUT ###########################################################

# data, indicators
num_months = 3
isNetwork = False
shouldBuildIndicators = False

# walk forward
percent = 20
runs = 14 # + 1 added later for final in-sample, use 15 of 16 cores available

# analyzer
opt = {
    'takeProfitPercent': [0.1], # np.linspace(0.25, 0.75, 5),
    'stopLossRatio': [0.5, 1], # np.linspace(0.1, 1, 10),
    'slowAngleFactor': [5] # np.linespace() np.linspace(0, 20, 5),
}

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
csv_filename = 'data/' + data_name + '.csv'
parent_path = 'wfa/' + data_name
path = parent_path + '/' + str(percent) + '_' + str(runs)

# get ohlc prices
data = utils.getOhlc(num_months, isNetwork)

# build indicators
if shouldBuildIndicators: build_indicators(data, parent_path)
emas = unpack('emas', parent_path)
slopes = unpack('slopes', parent_path)
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
    slopes = slopes,
    fractals = fractals,
    opt = opt,
    path = path)

# multiprocessing use all cores
cores = multiprocessing.cpu_count() # 16 available
cores -= 1 # leave 1 for basic computer tasks
fitnesses = [fitness for fitness in Fitness]

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
wfa.save()
print_metrics(get_walk_forward_results_metrics(wfa))

# print last in-sample analyzer
IS_path = wfa.path + '/' + str(runs)
analyzer_metrics = unpack('analyzer', IS_path)['metrics']
print_metrics(analyzer_metrics)

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')

# plot results
wfa.plot_equity()