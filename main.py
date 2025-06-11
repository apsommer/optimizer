import multiprocessing
import os
import time

import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, Process
from analysis.Analyzer import load_result
from analysis.Engine import Engine
from analysis.WalkForward import WalkForward
from strategy.LiveStrategy import LiveStrategy
from utils import DataUtils as repo
from utils.EngineUtils import print_metrics
from utils.PlotUtils import *

# INPUT ###########################################################

# data
num_months = 3
isNetwork = False

# analyzer
percent = 20
runs = 10

###################################################################

os.system('clear')
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

# multiprocessing use all cores, 16 available
processes = []
for run in range(runs+1):
    process = Process(
        target = wfa.walk_forward,
        args = (run,))
    processes.append(process)
    process.start()

# start threads
os.system('clear')
for process in processes:
    process.join()

# build composite of OS runs
engine = wfa.build_composite()

# get last IS analyzer
IS_path = wfa.path + str(runs)
analyzer_metrics = load_result('analyzer', IS_path)['metrics']

# print results
print_metrics(wfa.metrics)
print_metrics(analyzer_metrics)
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