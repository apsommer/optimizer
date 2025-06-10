import multiprocessing
import os
import time

import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool
from analysis.Analyzer import walk_forward, Analyzer, load_result
from analysis.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils import DataUtils as repo
from utils.EngineUtils import print_metrics
from utils.PlotUtils import *

# INPUT ###########################################################

# data
num_months = 6
isNetwork = False

# analyzer
percent = 20
runs = 15

###################################################################

os.system('clear')
start_time = time.time()

# organize outputs
data_name = 'NQ_' + str(num_months) + 'mon'
path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'

# get ohlc prices
data = repo.getOhlc(num_months, isNetwork)

# # multiprocess use all cores! todo refactor to Pool?
# cores = multiprocessing.cpu_count()
# cores -= 1 # save one for basic computer operations
# processes = []
# for run in range(runs):
#
#     process = multiprocessing.Process(
#         target = walk_forward,
#         args = (run, percent, runs, data, path))
#     processes.append(process)
#     process.start()
#
# # start threads
# for process in processes:
#     process.join()

# todo one more IS run is needed, without accompanying OS
#  suggested params to engine proxy below

# build composite equity curve
equity = pd.Series()
trades = []
for run in range(runs):
    equity = equity._append(
        load_result(run, path)['cash_series'])
    trades.extend(
        load_result(run, path)['trades'])

# mask data using equity curve index
OS = data.loc[equity.index, :]
params = load_result(0, path)['params'] # todo get params from last IS
strategy = LiveStrategy(OS, params)
engine = Engine(100, strategy)

engine.cash_series = equity
engine.trades = trades
engine.analyze() # do not run!

engine.print_trades()
print_metrics(engine.metrics)

plot_equity(engine)
# plot_trades(engine)






###################################################################
elapsed = time.time() - start_time
pretty = time.strftime('%H:%M:%S', time.gmtime(elapsed))
print(f'Elapsed time: {pretty}')



