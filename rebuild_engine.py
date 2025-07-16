import warnings

from utils.metrics import print_metrics
from utils.utils import *

''' rebuild single engine '''
# INPUT ###########################################################

path = 'genetic/NQ_12mon/generations/9'
id = 33

###################################################################

os.system('clear')
warnings.filterwarnings('ignore')
start_time = time.time()

# unpack bin
engine = unpack(id, path)
id = engine['id']
params = engine['params']
metrics = engine['metrics']

# display results
print_metrics(metrics)

