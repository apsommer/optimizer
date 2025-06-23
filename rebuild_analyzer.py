
import warnings
from analysis.Engine import Engine
from common import init_engine
from strategy.FastParams import FastParams
from strategy.FastStrategy import FastStrategy
from utils.metrics import print_metrics
from utils.utils import *

''' rebuild single analyzer '''
# INPUT ###########################################################

# finished analyzer
path = 'wfa/NQ_3mon/20_14/14'
id = 'analyzer'

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# unpack bin
bin = unpack(id, path)
id = bin['id']
metrics = bin['metrics']
fittest = bin['fittest']

# print results
print_metrics(metrics)
