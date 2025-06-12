import multiprocessing
import os
import time
import warnings

import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, Process
from analysis.Analyzer import load_result
from analysis.Engine import Engine
from analysis.WalkForward import WalkForward
from strategy.LiveStrategy import LiveStrategy
from utils import DataUtils as repo
from utils.MetricUtils import print_metrics, get_walk_forward_metrics
from utils.PlotUtils import *

# INPUT ###########################################################

# data
num_months = 3
isNetwork = False

# analyzer
percent = 20
runs = 14

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
    data = data)

# multiprocessing use all cores
cores = multiprocessing.cpu_count() # 16 available
cores -= 1 # leave one for basic computer tasks
_runs = range(runs + 1) # one more for last OS

# print header metrics
print_metrics(wfa.metrics)
print()

# automate pool of threads
pool = Pool(cores)
pool.map(wfa.walk_forward, _runs)
pool.close()
pool.join() # start one thread on each core

# build composite of OS runs
engine = wfa.build_composite()

# get last IS analyzer
# IS_path = wfa.path + str(runs)
# analyzer_metrics = load_result('analyzer', IS_path)['metrics']
# print_metrics(analyzer_metrics)

# print results
print()
print_metrics(get_walk_forward_metrics(wfa))
print_metrics(engine.metrics)
engine.print_trades()

###################################################################
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')

# plot results
plot_equity(engine)
# plot_trades(engine)
# plot_strategy(engine)