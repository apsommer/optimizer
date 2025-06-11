import multiprocessing
import os
import time

import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool
from analysis.Analyzer import load_result
from analysis.Engine import Engine
from analysis.walk_forward import walk_forward
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
runs = 3

###################################################################

os.system('clear')
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'

# get ohlc prices
data = repo.getOhlc(num_months, isNetwork)

# multiprocess use all cores! todo refactor to Pool?
cores = multiprocessing.cpu_count()
cores -= 1 # save one for basic computer operations

processes = []
for run in range(runs+1):

    process = multiprocessing.Process(
        target = walk_forward,
        args = (run, num_months, percent, runs, data))
    processes.append(process)
    process.start()

# start threads
for process in processes:
    process.join()

# build composite engine
equity = pd.Series()
trades = []
for run in range(runs):
    equity = equity._append(
        load_result(run, path)['cash_series'])
    trades.extend(
        load_result(run, path)['trades'])

# mask data to OS sample
OS = data.loc[equity.index, :]



params = load_result(0, path)['params'] # todo get params from last IS

# create engine, but don't run!
strategy = LiveStrategy(OS, params)
engine = Engine(100, strategy)

# finish engine build
engine.cash_series = equity
engine.trades = trades
engine.analyze()

# print results
engine.print_trades()
print_metrics(engine.metrics)

# plot results
plot_equity(engine)
# plot_trades(engine)
# plot_strategy(engine)

###################################################################
elapsed = time.time() - start_time
pretty = time.strftime('%-Hh %-Mm %-Ss', time.gmtime(elapsed))
print(f'Elapsed time: {pretty}')



