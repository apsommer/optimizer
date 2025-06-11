''' required top-level for multiprocessing '''
from analysis.Analyzer import Analyzer, load_result
from analysis.Engine import Engine
from strategy.LiveStrategy import LiveStrategy
from utils.EngineUtils import print_metrics, get_max_metric


def walk_forward(run, percent, runs, data, path):

    ###### in-sample
    IS_path = path + str(run) + '/'

    # isolate training xet
    IS_len = int(len(data) / ((percent / 100) * runs + 1))
    OS_len = int((percent / 100) * IS_len)
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
    print(f'\t*[{max_profit_id}]\n')
    params = load_result(max_profit_id, analyzer.path)['params']

    ###### out-of-sample
    # last run skip OS!
    if run == runs:
        return

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

def sweep_IS(fitness=0):
    pass
