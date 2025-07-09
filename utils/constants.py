import seaborn as sns

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

white = '#ffffff'
light_gray = '#9e9e9e'
dark_gray = '#525252'
dark_black = '#141414'
light_black = '#2e2e2e'

initial_cash = 10000

# # todo tradingview limitation ~20k bars
# tv_start = pd.Timestamp('2025-05-27T18:00:00', tz='America/Chicago')
# if tv_start > idx:
#     return
