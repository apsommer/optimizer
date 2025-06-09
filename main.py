import multiprocessing
import os
import time
from datetime import datetime, timedelta
from multiprocessing.queues import Queue

from analysis.Analyzer import Analyzer
from analysis.Engine import Engine
from utils.EngineUtils import print_metrics, get_max_metric
from utils import DataUtils as repo
from strategy.LiveStrategy import LiveStrategy

# INPUT ###########################################################

# data
num_months = 1
isNetwork = False

# analyzer
percent = 25
runs = 4

###################################################################

def walk_forward(run):

    # get ohlc prices
    data_name = 'NQ_' + str(num_months) + 'mon'
    csv_filename = 'data/' + data_name + '.csv'
    td = timedelta(days = num_months * 30.437)
    data = repo.getOhlc(
        starting_date = (datetime.now() - td).strftime("%Y-%m-%d"),
        ending_date = datetime.now().strftime("%Y-%m-%d"),
        csv_filename = csv_filename,
        isNetwork = isNetwork)

    # isolate training and testing sets
    IS_len = int(len(data) / ((percent / 100) * runs + 1))
    OS_len = int((percent / 100) * IS_len)

    # init first window
    IS_start, IS_end = 0, IS_len
    OS_start, OS_end = IS_len, IS_len + OS_len

    # organize output
    OS_path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'
    IS_path = OS_path + str(run) + '/'

    # mask training and testing sets
    IS = data.iloc[IS_start:IS_end]
    OS = data.iloc[OS_start:OS_end]

    # run exhaustive sweep over IS
    analyzer = Analyzer(run, IS, IS_path)
    analyzer.run()
    print_metrics(analyzer.metrics)

    # get result with highest profit
    max_profit = get_max_metric(analyzer, 'profit')
    max_profit_id = max_profit[0].id
    print(f'\t*[{max_profit_id}]\n')
    params = analyzer.load_result(max_profit_id)['params']

    # run strategy blind over OS with best params
    strategy = LiveStrategy(OS, params)
    engine = Engine(run, strategy)
    engine.run()
    engine.save(OS_path)

    # print engine metrics
    print_metrics(engine.metrics)

    # slide window forward
    IS_start += OS_len
    IS_end += OS_len
    OS_start += OS_len
    OS_end += OS_len

    # print_metrics(engine.metrics)
    # engine.print_trades()
    # engine = analyzer.rebuild_engine(id)
    # plot_equity(engine)
    # plot_strategy(engine)

os.system('clear')
start_time = time.time()

# todo multiprocess use all cores!
cores = multiprocessing.cpu_count()
print(f'cores: {cores}')

processes = []
for run in range(runs):

    process = multiprocessing.Process(
        target=walk_forward,
        args=(run,))
    processes.append(process)
    process.start()

for process in processes:
    process.join()

end_time = time.time()
print(f'\nElapsed time: {round(end_time - start_time)} seconds')



