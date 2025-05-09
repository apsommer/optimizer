import matplotlib.pyplot as plt
import Repository as repo
from Engine import Engine
from SMACrossoverStrategy import SMACrossoverStrategy
import logging

plt.rcParams['figure.figsize'] = [20, 12]
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# get ohlc prices
csv_filename = "data/nq_3months_2025-02-01_2025-05-01.csv"
data = repo.getOhlc(csv_filename=csv_filename) # repo.getOhlc()
data['sma_12'] = data.Close.rolling(12).mean()
data['sma_24'] = data.Close.rolling(24).mean()

# init engine
engine = Engine(initial_cash=1_000_000)
engine.add_data(data)
engine.add_strategy(SMACrossoverStrategy())

stats = engine.run()

# print
print("")
print("Performance:")
print("")
for stat, value in stats.items():
    print("{}: {}".format(stat, round(value, 5)))
print("")
plt.plot(data['Close'])
plt.show()