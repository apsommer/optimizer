import matplotlib.pyplot as plt
import Repository as repo
from Engine import Engine
from ExampleStrategy import ExampleStrategy
plt.rcParams['figure.figsize'] = [20, 12]

class SMACrossover(ExampleStrategy):
    def on_bar(self):
        if self.position_size == 0:
            if self.data.loc[self.current_idx].sma_12 > self.data.loc[self.current_idx].sma_24:
                limit_price = self.close * 0.995
                # BUY AS MANY SHARES AS WE CAN!
                order_size = self.cash / limit_price
                self.buy_limit('AAPL', size=order_size, limit_price=limit_price)
        elif self.data.loc[self.current_idx].sma_12 < self.data.loc[self.current_idx].sma_24:
            limit_price = self.close * 1.005
            self.sell_limit('AAPL', size=self.position_size, limit_price=limit_price)

# get ohlc prices
csv_filename = "data/nq_6months_2024-09-15_2025-03-15.csv"
ohlc = repo.getOhlc(csv_filename=csv_filename)
ohlc['sma_12'] = ohlc.Close.rolling(12).mean()
ohlc['sma_24'] = ohlc.Close.rolling(24).mean()

# init engine
engine = Engine(initial_cash=1_000_000)
engine.add_data(ohlc)
engine.add_strategy(SMACrossover())
stats = engine.run()

# print
print("")
print("Performance:")
print("")
for stat, value in stats.items():
    print("{}: {}".format(stat, round(value, 5)))
print("")
plt.plot(ohlc['Close'])
plt.show()