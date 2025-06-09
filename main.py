import multiprocessing
import os
import time

from tqdm import tqdm
from multiprocessing import Pool
from analysis.Analyzer import walk_forward
from utils import DataUtils as repo

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

# multiprocess use all cores! todo refactor to Pool?
cores = multiprocessing.cpu_count()
cores -= 1 # save one for basic computer operations
processes = []
for run in range(runs):

    process = multiprocessing.Process(
        target = walk_forward,
        args = (run, percent, runs, data, path))
    processes.append(process)
    process.start()

# start threads
for process in processes:
    process.join()

# todo stitch OS samples into composite engine

###################################################################
end_time = time.time()
print(f'\nElapsed time: {round(end_time - start_time)} seconds')



