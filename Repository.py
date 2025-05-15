import logging
import sys
import databento as db
import pandas as pd
import local.api_keys as keys

log_format = "%(message)s"
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=log_format)

def logm(message):
        logging.info(message)

def getOhlc(
    csv_filename = None,
    symbol = "NQ.v.0",
    schema = "ohlcv-1m",
    starting_date = "2025-02-01",
    ending_date = "2025-05-01"):

    # return cached data in csv format
    if csv_filename is not None:

        ohlc = pd.read_csv(csv_filename, index_col=0)
        ohlc.index = pd.to_datetime(ohlc.index)

        logm("Uploaded OHLC from " + csv_filename)
        return ohlc

    # request network data synchronous!
    client = db.Historical(keys.bento_api_key)
    ohlc = (client.timeseries.get_range(
        dataset = "GLBX.MDP3",
        symbols = [symbol],
        stype_in = "continuous",
        schema = schema,
        start = starting_date,
        end = ending_date)
            .to_df())

    logm("Downloaded OHLC from databento, costs $$$ ...")

    # rename, drop
    ohlc.rename(columns = {"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace = True)
    ohlc.index.rename("timestamp", inplace = True)
    ohlc = ohlc[ohlc.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id', 'volume'])]

    # normalize timestamps
    ohlc.index = ohlc.index.tz_localize(None)
    ohlc.index = pd.to_datetime(ohlc.index)

    csv_filename = "data/nq_3months_2025-02-01_2025-05-01.csv"
    ohlc.to_csv(csv_filename)

    return ohlc