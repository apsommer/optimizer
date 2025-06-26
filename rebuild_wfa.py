
import warnings
from analysis.Engine import Engine
from common import init_engine
from strategy.FastParams import FastParams
from strategy.FastStrategy import FastStrategy
from utils.metrics import print_metrics
from utils.utils import *

''' rebuild wfa '''
# INPUT ###########################################################

# finished wfa
path = 'wfa/NQ_10mon/25_14'
id = 'wfa'

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# unpack bin
bin = unpack(id, path)
best_params = bin['best_params']
best_fitness = bin['best_fitness']
metrics = bin['metrics']

# print results
print_metrics(metrics)
