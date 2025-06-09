import multiprocessing
import os
import time
from datetime import datetime, timedelta
from analysis.Analyzer import walk_forward
from utils import DataUtils as repo

# INPUT ###########################################################

# data
num_months = 1
isNetwork = False

# analyzer
percent = 20
runs = 5

###################################################################

os.system('clear')
start_time = time.time()

# get ohlc prices
data_name = 'NQ_' + str(num_months) + 'mon'
csv_filename = 'data/' + data_name + '.csv'
td = timedelta(days=num_months * 30.437)
data = repo.getOhlc(
    starting_date=(datetime.now() - td).strftime("%Y-%m-%d"),
    ending_date=datetime.now().strftime("%Y-%m-%d"),
    csv_filename=csv_filename,
    isNetwork=isNetwork)

# organize output
path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'

# multiprocess use all cores!
processes = []
for run in range(runs):
    process = multiprocessing.Process(
        target=walk_forward,
        args=(run, percent, runs, data, path))
    processes.append(process)
    process.start()

# start threads
for process in processes:
    process.join()

# todo stitch OS samples into composite engine

end_time = time.time()
print(f'\nElapsed time: {round(end_time - start_time)} seconds')



