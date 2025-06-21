import multiprocessing
import os
import random
import re
import shutil
import time
import warnings

import pandas as pd
from numpy import linspace
from tqdm import tqdm
from multiprocessing import Pool, Process

from analysis.Engine import Engine
from analysis.WalkForward import WalkForward

from model.Fitness import Fitness
from strategy.LiveStrategy import LiveStrategy
from utils import utils
from utils.utils import unpack
from utils.metrics import print_metrics, get_walk_forward_results_metrics
from utils.plots import *

# INPUT ###########################################################

# data
num_months = 14
isNetwork = False

# walk forward
percent = 20
runs = 14 # + 1 added later for final IS, 16 cores available

# analyzer
num = 5
opt = {
    'takeProfitPercent': linspace(.30, .65, num=num, dtype=float),
    'fastAngleFactor': linspace(5, 45, num=num, dtype=int),
    'timeout': linspace(1, 4, num=num, dtype=float)
}

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
csv_filename = 'data/' + data_name + '.csv'
path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs)

# remove any residual analyses
shutil.rmtree(path, ignore_errors=True)

# get ohlc prices
data = utils.getOhlc(num_months, isNetwork)
if not isNetwork: print(f'Upload OHLC from { csv_filename }')

# create averages
create_indicators(data, path)

# init walk forward
wfa = WalkForward(
    num_months = num_months,
    percent = percent,
    runs = runs,
    data = data,
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
plot_equity(wfa)