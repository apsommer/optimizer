import databento as db
import pandas as pd
import local.api_keys as keys

def getOhlc(
    csv_filename = None,
    symbol = "NQ.v.0",
    schema = "ohlcv-1m",
    starting_date = "2025-04-25",
    ending_date = "2025-05-25"):

    # return cached data in csv format
    if csv_filename is not None:

        ohlc = pd.read_csv(csv_filename, index_col=0)
        ohlc.index = pd.to_datetime(ohlc.index)

        print("\nUploaded OHLC from " + csv_filename)
        return ohlc

    print("\nDownloaded OHLC from databento, costs $$$ ...")
    csv_filename = "nq_1mon.csv"

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

    # rename, drop
    ohlc.rename(columns = {"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace = True)
    ohlc.index.rename("timestamp", inplace = True)
    ohlc = ohlc[ohlc.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id', 'volume'])]

    # normalize timestamps
    ohlc.index = ohlc.index.tz_localize(None)
    ohlc.index = pd.to_datetime(ohlc.index)

    # save to disk
    ohlc.to_csv(csv_filename)
    return ohlc