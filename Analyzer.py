import matplotlib.pyplot as plt
import Repository as repo
from Engine import Engine
from HalfwayStrategy import HalfwayStrategy
import logging

plt.rcParams['figure.figsize'] = [20, 12]
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# get ohlc prices
csv_filename = "data/nq_3months_2025-02-01_2025-05-01.csv"
data = repo.getOhlc(csv_filename=csv_filename) # repo.getOhlc()

# init engine
engine = Engine(initial_cash = 1000)
engine.add_data(data)
engine.add_strategy(HalfwayStrategy())
stats = engine.run()
engine.plot()

# print
print("")
print("Performance:")
print("")
for stat, value in stats.items():
    print("{}: {}".format(stat, round(value, 5)))
print("")
# print(engine.trades)

# plt.plot(data['Close'])
plt.show()
