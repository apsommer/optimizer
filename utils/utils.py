import os
import os
import pickle
import shutil
from datetime import timedelta, datetime

import databento as db
import finplot as fplt
import pandas as pd
import pytz
from PyQt6.QtGui import QFont
from tqdm import tqdm

import local.api_keys as keys
from utils.constants import *

def getOhlc(asset, num_months, isNetwork = False):

    # organize outputs
    data_name = asset + '_' + str(num_months) + 'm'
    path = 'data/' + data_name
    csv_filename = data_name + '.csv'
    csv_filepath = path + '/' + csv_filename

    # set timezone to exchange
    timezone = 'America/Chicago'

    # return local cache
    if not isNetwork:

        print(f'Upload ohlc from {csv_filename}')

        try:
            ohlc = pd.read_csv(csv_filepath, index_col = 0)
            ohlc.index = timestamp(ohlc, timezone)

        except FileNotFoundError:
            os.system('clear')
            print(f'{csv_filename} does not exist, download $$$?')
            exit()

        return ohlc

    print(f'$$$ Download ohlc from databento as {csv_filename}')

    # construct symbol
    # https://databento.com/docs/standards-and-conventions/symbology#continuous?historical=python&live=python&reference=python
    symbol = asset + '.v.0' # ["NQ.v.0"], # [ticker].v.[expiry]

    # timespan
    delta = timedelta(days = num_months * 30.437)
    starting_date = (datetime.now() - delta).strftime("%Y-%m-%d") # trump elected 051124
    ending_date = datetime.now().strftime("%Y-%m-%d") # '2025-07-24'

    # request network data, costs $$$, synchronous
    ohlc = db.Historical(keys.db).timeseries.get_range(
        dataset = 'GLBX.MDP3',
        symbols = symbol,
        stype_in = 'continuous',
        schema = 'ohlcv-1m',
        start = starting_date,
        end = ending_date
    )

    # rename, drop, timestamp
    ohlc = ohlc.to_df()
    ohlc.rename(columns = {"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace = True)
    ohlc.index.rename("timestamp", inplace = True)
    ohlc = ohlc[ohlc.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id', 'volume'])]
    ohlc.index = timestamp(ohlc, timezone)

    # remove residual data and indicators
    shutil.rmtree(path, ignore_errors = True)
    os.makedirs(path)

    # save to disk
    ohlc.to_csv(csv_filepath)
    return ohlc

def timestamp(data, timezone):
    utc = pd.to_datetime(data.index, utc = True)
    return utc.tz_convert(timezone)

def getIndicators(data, opt, path):

    # check emas
    shouldBuildEmas = False
    try:

        emas = unpack('emas', path)
        for fastMinutes in opt.fastMinutes:
            if 'ema_' + str(fastMinutes) not in emas.columns:
                shouldBuildEmas = True
        for slowMinutes in opt.slowMinutes:
            if 'ema_' + str(slowMinutes) not in emas.columns:
                shouldBuildEmas = True

    except FileNotFoundError:
        shouldBuildEmas = True

    # build emas, if needed
    if shouldBuildEmas:
        print(f'\nIndicators:')
        emas = build_emas(data, opt, path)

    # check fractals and build, if needed
    try:
        fractals = unpack('fractals', path)
    except FileNotFoundError:
        fractals = build_fractals(data, path)

    return emas, fractals

def build_emas(data, opt, path):

    # define ema window lengths
    mins = []
    mins.extend(opt.fastMinutes)
    mins.extend(opt.slowMinutes)

    # init container
    emas = pd.DataFrame(index = data.index)

    for min in tqdm(
        iterable = mins,
        colour = yellow,
        bar_format = '        Averages:       {percentage:3.0f}%|{bar:80}{r_bar}'):

        # column names
        col_ema = 'ema_' + str(min)
        col_slope = 'slope_' + str(min)
        col_long = 'long_' + str(min)
        col_short = 'short_' + str(min)

        # smooth averages
        smooth = round(0.2 * min)

        raw = pd.Series(data.Open).ewm(span = min).mean()
        smoothed = raw.ewm(span = smooth).mean()
        emas.loc[:, col_ema] = smoothed

        # slope of average
        slope = get_slope(smoothed)
        emas.loc[:, col_slope] = slope

        # build trend counts
        longMinutes = 0
        shortMinutes = 0
        for idx in tqdm(
            leave = False,
            position = 1,
            iterable = data.index,
            colour = aqua,
            bar_format = '                        {percentage:3.0f}%|{bar:80}{r_bar}'):

            if slope[idx] > 0:
                longMinutes += 1
                shortMinutes = 0
            else:
                longMinutes = 0
                shortMinutes += 1

            emas.loc[idx, col_long] = longMinutes
            emas.loc[idx, col_short] = shortMinutes

    save(emas, 'emas', path)
    return emas

def get_slope(series):

    slope = pd.Series(index = series.index)
    prev = series.iloc[0]

    for idx, value in series.items():
        if idx == series.index[0]: continue
        slope[idx] = ((value - prev) / prev) * 100
        prev = value

    return np.rad2deg(np.atan(slope))

def build_fractals(data, path):

    # init container
    fractals = pd.DataFrame(
        data = np.nan,
        index = data.index,
        dtype = float,
        columns = ['buyFractal', 'sellFractal'])

    # fractal indicator
    buyPrice = np.nan
    sellPrice = np.nan

    for i in tqdm(
        iterable = range(len(data.index)),
        colour = yellow,
        bar_format = '        Fractals:       {percentage:3.0f}%|{bar:80}{r_bar}'):

        # skip first 2 bars and last 2 bars, due to definition -2:+2
        if 2 > i or i > len(data.index) - 3: continue

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

        # stagger 2 minutes because can not see into the future
        fractals.iloc[i+2].buyFractal = buyPrice
        fractals.iloc[i+2].sellFractal = sellPrice

    save(fractals, 'fractals', path)
    return fractals

def init_plot(window, title):

    # window position, maximized
    fplt.winx = window * 3840
    fplt.winy = 0
    fplt.winw = 3840
    fplt.winh = 2160

    # background
    fplt.background = dark_black
    fplt.candle_bull_color = dark_gray
    fplt.candle_bull_body_color = dark_gray
    fplt.candle_bear_color = dark_gray
    fplt.candle_bear_body_color = dark_gray
    fplt.cross_hair_color = white

    # adjust timezone to CME exchange
    fplt.display_timezone = pytz.timezone('America/Chicago')

    # init finplot
    ax = fplt.create_plot(title=title)

    # get axis
    axis_pen = fplt._makepen(color = white)
    right = ax.axes['right']['item']
    bottom = ax.axes['bottom']['item']

    # set axis
    right.setPen(axis_pen)
    right.setTextPen(axis_pen)
    right.setTickPen(axis_pen)

    bottom.setPen(axis_pen)
    bottom.setTextPen(axis_pen)
    bottom.setTickPen(axis_pen)

    # set font
    font = QFont('Ubuntu', 16)
    right.setTickFont(font)
    bottom.setTickFont(font)

    # gridlines
    ax.set_visible(xgrid = True, ygrid = True)

    # crosshair
    ax.crosshair.vline.setPen(axis_pen)
    ax.crosshair.hline.setPen(axis_pen)

    # legend
    fplt.legend_fill_color = dark_black
    fplt.legend_border_color = None # dark_gray

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

    filehandler = open(path_filename, 'rb')
    return pickle.load(filehandler)

def format_timestamp(idx, type = 'tradingview'):

    formatter = '%b %d, %Y, %H:%M'
    if type != 'tradingview': formatter = '%Y%m%d_%H%M%S'

    return idx.strftime(formatter)
