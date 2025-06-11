''' required top-level for multiprocessing '''
from analysis.Analyzer import Analyzer, load_result
from analysis.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils.EngineUtils import print_metrics, get_max_metric

def walk_forward(run, num_months, percent, runs, data):

    # organize outputs
    data_name = 'NQ_' + str(num_months) + 'mon'
    path = 'wfa/' + data_name + '/' + str(percent) + '_' + str(runs) + '/'

    ###### in-sample
    IS_path = path + str(run) + '/'

    # isolate training xet
    IS_len = int(len(data) / ((percent / 100) * runs + 1))
    OS_len = int((percent / 100) * IS_len)

    params = sweep_IS(run, IS_path, IS_len, OS_len, data)

    # last run skip OS
    if run == runs: return

    run_OS(run, path, IS_len, OS_len, data, params)

def sweep_IS(run, IS_path, IS_len, OS_len, data, fitness=0):

    # isolate training xet
    IS_start = run * OS_len
    IS_end = IS_start + IS_len
    IS = data.iloc[IS_start:IS_end]

    # run exhaustive sweep over IS
    analyzer = Analyzer(run, IS, IS_path)
    analyzer.run()
    print_metrics(analyzer.metrics)

    # get result with highest profit
    max_profit = get_max_metric(analyzer, 'profit')
    max_profit_id = max_profit[0].id
    params = load_result(max_profit_id, analyzer.path)['params']

    print(f'\t*[{max_profit_id}]\n')
    return params

def run_OS(run, path, IS_len, OS_len, data, params):

    IS_start = run * OS_len
    IS_end = IS_start + IS_len

    OS_start = IS_end
    OS_end = OS_start + OS_len
    OS = data.iloc[OS_start:OS_end]

    # run strategy blind over OS with best params
    strategy = LiveStrategy(OS, params)
    engine = Engine(run, strategy)
    engine.run()
    engine.save(path)

    # print_metrics(engine.metrics)
    # engine.print_trades()