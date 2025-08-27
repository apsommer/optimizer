import random

import numpy as np
import seaborn as sns
import matplotlib as mpl

# finplot entities
white = '#ffffff'
light_gray = '#9e9e9e'
dark_gray = '#525252'
dark_black = '#141414'
light_black = '#5e5e5e'

# get color pallet from seaborn, 10 total
# https://seaborn.pydata.org/tutorial/color_palettes.html
# deep, muted, pastel, bright, dark, colorblind
colors = sns.color_palette('bright').as_hex()
blue = colors[0]
orange = colors[1]
green = colors[2]
red = colors[3]
purple = colors[4]
brown = colors[5]
pink = colors[6]
gray = colors[7]
yellow = colors[8]
aqua = colors[9]

# color ribbon
crest = sns.color_palette("crest", as_cmap = True)
ribbon_colors = crest(np.linspace(0, 1, 10))
def get_ribbon_color(i):
    return mpl.colors.rgb2hex(ribbon_colors[i % 10])

initial_cash = 10000

########################################################################################################################

# tradingview limitation ~20k bars
# tv_start = pd.Timestamp('2025-07-27T22:00:00', tz='America/Chicago')
# if tv_start > idx:
#     return