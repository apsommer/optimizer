import multiprocessing
import os
import random
import re
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
runs = 14 # + 1 added later for final IS, 16 cores available

# analyzer
num = 3
opt = {
    'disableEntryMinutes': linspace(60, 180, num=num, dtype=int),
    'fastMomentumMinutes': linspace(55, 130, num=num, dtype=int),
    'takeProfitPercent': linspace(.25, .70, num=2, dtype=float)
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
_fits = [ fitness for fitness in Fitness ]

# print header metrics
print_metrics(wfa.metrics)

def set_name():

    id = int(re.findall(
        pattern = r'\d+',
        string = multiprocessing.current_process().name)[0])

    id = (id - 1) % cores

    multiprocessing.current_process().name = str(id)

# run in-sample sweep
pool = Pool(
    processes = cores,
    initializer = set_name)
pool.map(wfa.sweep_IS, range(runs + 1)) # add 1 for last IS (prediction)
pool.close()
pool.join()

# run OS for each fitness
pool = Pool(
    processes = cores,
    initializer = set_name)
pool.map(wfa.run_OS, range(runs))
pool.close()
pool.join()

# build composite OS
pool = Pool(
    processes = cores,
    initializer = set_name)
pool.map(wfa.build_composite, _fits)
pool.close()
pool.join()

# select best fitness
wfa.analyze()
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