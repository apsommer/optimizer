import time
import databento as db
import pandas as pd
import local.api_keys as keys
import numpy as np

def getOhlc(
    csv_filename = None,
    symbol = "NQ.v.0",
    schema = "ohlcv-1m",
    starting_date = "2025-05-03",
    ending_date = time.strftime("%Y-%m-%d")):

    timezone = 'America/Chicago'

    # return cached data in csv format
    if csv_filename is not None:

        ohlc = pd.read_csv(csv_filename, index_col=0)
        ohlc.index = timestamp(ohlc, timezone)

        print(f'Uploaded OHLC from {csv_filename}')
        return ohlc

    print("Downloaded OHLC from databento, costs $$$ ...")

    # request network data synchronous! costs $!
    client = db.Historical(keys.bento_api_key)
    ohlc = (client.timeseries.get_range(
        dataset = "GLBX.MDP3",
        symbols = [symbol],
        stype_in = "continuous",
        schema = schema,
        start = starting_date,
        end = ending_date)
            .to_df())

    # rename, drop, timestamp
    ohlc.rename(columns = {"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace = True)
    ohlc.index.rename("timestamp", inplace = True)
    ohlc = ohlc[ohlc.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id', 'volume'])]
    ohlc.index = timestamp(ohlc, timezone)

    # save to disk
    csv_filename = "data/nq_1mon.csv"
    ohlc.to_csv(csv_filename)
    return ohlc

def timestamp(data, timezone):
    utc = pd.to_datetime(data.index)
    return utc.tz_convert(timezone)