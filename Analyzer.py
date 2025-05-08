import Repository as data
from LiveStrategy import LiveStrategy

# constants
csv_filename = "data/nq_6months_2024-09-15_2025-03-15.csv"
starting_date = "2024-09-15"
# csv_filename = "data/nq_2years_2023-03-15_2025-03-15.csv"
# starting_date = "2023-03-15"
ending_date = "2025-03-15"
symbol = "NQ.v.0"
schema = "ohlcv-1m"

# todo download prices costs $
# df_prices = data.getPrices(
#     symbol=symbol,
#     schema=schema,
#     starting_date=starting_date,
#     ending_date=ending_date)
# df_prices.to_csv(csv_filename)
# df_prices.to_excel(csv_filename.replace(".csv", ".xlsx"))

# todo read from csv instead
ohlc = data.getOhlc(csv_filename=csv_filename)

def run():

    # todo run test