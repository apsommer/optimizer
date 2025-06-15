import multiprocessing
import os
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
from utils import utils as repo
from utils.utils import load_result
from utils.metrics import print_metrics, get_walk_forward_results_metrics
from utils.plots import *

# INPUT ###########################################################

# data
num_months = 3
isNetwork = False

# walk forward
percent = 20
runs = 14 # + 1 added later for final IS

# analyzer
num = 2
opt = {
    'disableEntryMinutes': linspace(60, 180, num=num, dtype=int),
    'fastMomentumMinutes': linspace(55, 130, num=num, dtype=int),
    'takeProfitPercent': linspace(.25, .70, num=num, dtype=float)
}

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# get ohlc prices
data_name = 'NQ_' + str(num_months) + 'mon'
path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'
data = repo.getOhlc(num_months, isNetwork)

# init walk forward analysis
wfa = WalkForward(
    num_months = num_months,
    percent = percent,
    runs = runs,
    data = data,
    opt = opt)

# multiprocessing use all cores
cores = multiprocessing.cpu_count() # 16 available
cores -= 1 # leave 1 for basic computer tasks
_runs = range(runs + 1) # add 1 for last OS
_fits = [ fitness for fitness in Fitness ]

# print header metrics
print_metrics(wfa.metrics)

# run walk forward
pool = Pool(cores) # one core for each run
pool.map(wfa.walk_forward, _runs)
pool.close()
pool.join()

# build composite OS for each fitness function
bath = Pool(cores)
bath.map(wfa.build_composite, _fits)
bath.close()
bath.join() # start one process per core

print_metrics(get_walk_forward_results_metrics(wfa))

# print last IS analyzer
IS_path = wfa.path + str(runs)
analyzer_metrics = load_result('analyzer', IS_path)['metrics']
print_metrics(analyzer_metrics)

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')

# plot results
plot_equity(wfa)