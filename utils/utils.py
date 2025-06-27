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
from tqdm import tqdm

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

    print('Download OHLC from databento, costs $$$')

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

def build_indicators(data, path):

    print('Indicators:')

    build_emas(data, path)
    build_fractals(data, path)

def build_fractals(data, path):

    # init container
    fractals = pd.DataFrame(
        index = data.index,
        dtype = float,
        columns = ['buyFractal', 'sellFractal'])

    # fractal indicator
    buyPrice = data.iloc[0].High
    sellPrice = data.iloc[0].Low

    for i in tqdm(
        iterable = range(len(data.index)),
        colour = yellow,
        bar_format = '        Fractals:       {percentage:3.0f}%|{bar:100}{r_bar}'):

        # skip first 2 bars and last 2 bars
        if 2 < i < len(data.index) - 3:

            # update prices, if needed
            if (data.iloc[i].High > data.iloc[i-1].High
                and data.iloc[i].High > data.iloc[i-2].High
                and data.iloc[i].High > data.iloc[i+1].High
                and data.iloc[i].High > data.iloc[i+2].High):

                buyPrice = data.iloc[i].High

            if (data.iloc[i].Low < data.iloc[i-1].Low
                and data.iloc[i].Low < data.iloc[i-2].Low
                and data.iloc[i].Low < data.iloc[i+1].Low
                and data.iloc[i].Low < data.iloc[i+2].Low):

                sellPrice = data.iloc[i].Low

        fractals.iloc[i].buyFractal = buyPrice
        fractals.iloc[i].sellFractal = sellPrice

    save(fractals, 'fractals', path)

def build_emas(data, path):

    fastestMinutes = 25
    slowestMinutes = 2880
    num = 10

    ###################################################################

    # spread of averages from fastest to slowest
    mins = np.linspace(fastestMinutes, slowestMinutes, num)

    # init containers
    emas = pd.DataFrame(index = data.index)
    slopes = pd.DataFrame(index = data.index)

    for min in tqdm(
        iterable = mins,
        colour = yellow,
        bar_format = '        Averages:       {percentage:3.0f}%|{bar:100}{r_bar}'):

        # smooth averages
        smooth = round(0.2 * min)

        raw = pd.Series(data.Open).ewm(span = min).mean()
        smoothed = raw.ewm(span = smooth).mean()
        slope = get_slope(smoothed)

        emas.loc[:, min] = smoothed
        slopes.loc[:, min] = slope

    save(emas, 'emas', path)
    save(slopes, 'slopes', path)

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

    # background
    fplt.background = light_black
    fplt.candle_bull_color = dark_gray
    fplt.candle_bull_body_color = dark_gray
    fplt.candle_bear_color = dark_gray
    fplt.candle_bear_body_color = dark_gray
    fplt.cross_hair_color = white

    # todo font size

    # init finplot
    ax = fplt.create_plot(title=title)

    # axis
    axis_pen = fplt._makepen(color = gray)
    ax.axes['right']['item'].setPen(axis_pen)
    ax.axes['right']['item'].setTextPen(axis_pen)
    ax.axes['right']['item'].setTickPen(axis_pen)
    ax.axes['bottom']['item'].setPen(axis_pen)
    ax.axes['bottom']['item'].setTextPen(axis_pen)
    ax.axes['bottom']['item'].setTickPen(axis_pen)

    # gridlines
    ax.set_visible(xgrid = True, ygrid = True)

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