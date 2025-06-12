import time
from datetime import timedelta, datetime

import databento as db
import pandas as pd
import local.api_keys as keys
import numpy as np

def getOhlc(num_months, isNetwork):

    data_name = 'NQ_' + str(num_months) + 'mon'
    csv_filename = 'data/' + data_name + '.csv'
    td = timedelta(days=num_months * 30.437)

    starting_date = (datetime.now() - td).strftime("%Y-%m-%d")
    ending_date = datetime.now().strftime("%Y-%m-%d")
    timezone = 'America/Chicago'

    # return local cache
    if not isNetwork:

        ohlc = pd.read_csv(csv_filename, index_col=0)
        ohlc.index = timestamp(ohlc, timezone)

        print(f'Upload OHLC from {csv_filename}\n')
        return ohlc

    print("Download OHLC from databento, $$$ ...\n")

    # request network data synchronous! costs $!
    client = db.Historical(keys.bento_api_key)
    ohlc = (client.timeseries.get_range(
        dataset = "GLBX.MDP3",
        symbols = ["NQ.v.0"],
        stype_in = "continuous",
        schema = "ohlcv-1m",
        start = starting_date,
        end = ending_date)
            .to_df())

    # rename, drop, timestamp
    ohlc.rename(columns = {"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace = True)
    ohlc.index.rename("timestamp", inplace = True)
    ohlc = ohlc[ohlc.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id', 'volume'])]
    ohlc.index = timestamp(ohlc, timezone)

    # save to disk
    ohlc.to_csv(csv_filename)
    return ohlc

def timestamp(data, timezone):
    utc = pd.to_datetime(data.index, utc=True)
    return utc.tz_convert(timezone)