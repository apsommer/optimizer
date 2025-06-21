import multiprocessing
import os
import pickle
import re
import time
from datetime import timedelta, datetime
from inspect import trace

import databento as db
import pandas as pd
from sympy.plotting.textplot import linspace

import local.api_keys as keys
import numpy as np
import finplot as fplt
from utils.constants import *

def getOhlc(num_months, isNetwork):

    data_name = 'NQ_' + str(num_months) + 'mon'
    csv_filename = 'data/' + data_name + '.csv'
    td = timedelta(days=num_months * 30.437)
    starting_date = (datetime.now() - td).strftime("%Y-%m-%d")
    ending_date = datetime.now().strftime("%Y-%m-%d") # '2025-06-13'
    timezone = 'America/Chicago'

    # return local cache
    if not isNetwork:

        ohlc = pd.read_csv(csv_filename, index_col=0)
        ohlc.index = timestamp(ohlc, timezone)

        print(f'Upload OHLC from {csv_filename}')
        return ohlc

    print('Download OHLC from databento $$$')

    # request network data synchronous
    client = db.Historical(keys.bento_api_key) # $$$
    ohlc = (client.timeseries.get_range(
        dataset = "GLBX.MDP3",
        symbols = ["NQ.v.0"],
        stype_in = "continuous",
        schema = "ohlcv-1m",
        start = starting_date,
        end = ending_date
    ).to_df())

    # rename, drop, timestamp
    ohlc.rename(columns = {"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace = True)
    ohlc.index.rename("timestamp", inplace = True)
    ohlc = ohlc[ohlc.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id', 'volume'])]
    ohlc.index = timestamp(ohlc, timezone)

    # save to disk
    ohlc.to_csv(csv_filename)
    return ohlc

def timestamp(data, timezone):
    utc = pd.to_datetime(data.index, utc = True)
    return utc.tz_convert(timezone)

def set_process_name():

    cores = multiprocessing.cpu_count()  # 16 available
    cores -= 1  # leave 1 for basic computer tasks

    # extract numerical digits from default process name, 1-based
    id = int(re.findall(
        pattern = r'\d+',
        string = multiprocessing.current_process().name)[0])

    id = (id - 1) % cores
    multiprocessing.current_process().name = str(id)

def create_avgs(data, path):

    minutes = np.linspace(525, 2525, 10, dtype = int)

    avgs = pd.DataFrame(
        index = data.index)

    for minute in minutes:

        smooth = minute / 5

        raw = pd.Series(data.Open).ewm(span = minute).mean()
        avg = raw.ewm(span = smooth).mean()
        slope = get_slope(avg)

        avg_key = 'avg_' + str(minute)
        slope_key = 'slope_' + str(minute)
        avgs.loc[:, avg_key] = avg
        avgs.loc[:, slope_key] = slope

    save(
        bundle = avgs,
        filename = 'avgs',
        path = path)

def create_indicators(data, path):

    fastMinutes = 25
    slowMinutes = 2555

    # calculate raw averages
    rawFast = pd.Series(data.Open).ewm(span=fastMinutes).mean()
    rawSlow = pd.Series(data.Open).ewm(span=slowMinutes).mean()
    fast = rawFast.ewm(span=5).mean()
    slow = rawSlow.ewm(span=200).mean()
    fastSlope = get_slope(fast)
    slowSlope = get_slope(slow)

    # persist
    indicators = pd.DataFrame(index=data.index)
    indicators['fast'] = fast
    indicators['slow'] = slow
    indicators['fastSlope'] = fastSlope
    indicators['slowSlope'] = slowSlope

    save(
        bundle = indicators,
        filename = 'indicators',
        path = path)

def get_slope(series):

    slope = pd.Series(index=series.index)
    prev = series.iloc[0]

    for idx, value in series.items():
        if idx == series.index[0]: continue
        slope[idx] = ((value - prev) / prev) * 100
        prev = value

    return np.rad2deg(np.atan(slope))

def init_plot(pos, title):

    # window position, maximized
    fplt.winx = pos * 3840
    fplt.winy = 0
    fplt.winw = 3840
    fplt.winh = 2160

    # background todo font size
    fplt.background = light_black
    fplt.candle_bull_color = light_gray
    fplt.candle_bull_body_color = light_gray
    fplt.candle_bear_color = dark_gray
    fplt.candle_bear_body_color = dark_gray
    fplt.cross_hair_color = white

    # init finplot
    ax = fplt.create_plot(title=title)

    # axis
    axis_pen = fplt._makepen(color = gray)
    ax.axes['right']['item'].setPen(axis_pen)
    ax.axes['right']['item'].setTextPen(axis_pen)
    ax.axes['right']['item'].setTickPen(None)
    ax.axes['bottom']['item'].setPen(axis_pen)
    ax.axes['bottom']['item'].setTextPen(axis_pen)
    ax.axes['bottom']['item'].setTickPen(None)

    # crosshair
    ax.crosshair.vline.setPen(axis_pen)
    ax.crosshair.hline.setPen(axis_pen)

    return ax

''' serialize '''
def save(bundle, filename, path):

    # make directory, if needed
    if not os.path.exists(path):
        os.makedirs(path)

    # create new binary
    path_filename = path + '/' + filename + '.bin'

    filehandler = open(path_filename, 'wb')
    pickle.dump(bundle, filehandler)

''' deserialize '''
def unpack(id, path):

    filename = str(id) + '.bin'
    path_filename = path + '/' + filename

    try:
        filehandler = open(path_filename, 'rb')
        return pickle.load(filehandler)
    except FileNotFoundError:
        print(f'\n{path_filename} not found')
        exit()