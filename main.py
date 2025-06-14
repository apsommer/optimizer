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
from model.Fitness import Fitness
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
runs = 15

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
# cores -= 1 # leave 1 for basic computer tasks

# print header metrics
print_metrics(wfa.metrics)

# automate pool of threads
pool = Pool(cores)
pool.map(wfa.walk_forward, range(runs + 1))
pool.close()
pool.join() # start one thread on each core

# build composite of OS runs
wfa.build_composites()
print_metrics(get_walk_forward_metrics(wfa))

# todo debug get last IS analyzer
IS_path = wfa.path + str(runs)
analyzer_metrics = load_result('analyzer', IS_path)['metrics']
print_metrics(analyzer_metrics)

# print analysis time
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'\nElapsed time: {pretty}')

# plot results
print('Plot:')
# plot_trades(engine)
plot_equity(wfa)
# # plot_strategy(engine)