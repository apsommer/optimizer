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
from utils.PlotUtils import plot_equity

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
for run in range(runs):
    equity = equity._append(
        load_result(run, path)['cash_series'])
    # todo rebuild trades

# mask data using equity curve index
OS = data.loc[equity.index, :]
params = load_result(0, path)['params'] # todo get params from last IS
strategy = LiveStrategy(OS, params)
engine = Engine(100, strategy)

# no need to run!
engine.cash_series = equity
plot_equity(engine)




###################################################################
elapsed = time.time() - start_time
pretty = time.strftime('%H:%M:%S', time.gmtime(elapsed))
print(f'Elapsed time: {pretty}')



