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

first_result = load_result(0, path)

# build composite equity curve
equity = pd.Series()

# loop each bar
for run in tqdm(
    # disable = True,
    iterable = range(runs),
    colour = 'BLUE',
    bar_format = '{percentage:3.0f}%|{bar:100}{r_bar}'):

    result = load_result(run, path)
    cash_series = result['cash_series']
    equity = equity._append(cash_series)

# mask data using equity curve index
masked_data = data.loc[equity.index, :]

params = first_result['params'] # arbitrary
strategy = LiveStrategy(masked_data, params)
engine = Engine(100, strategy)

# no need to run!
engine.cash_series = equity
# todo engine trades
plot_equity(engine)




###################################################################
elapsed = time.time() - start_time
pretty = time.strftime('%H:%M:%S', time.gmtime(elapsed))
print(f'Elapsed time: {pretty}')



