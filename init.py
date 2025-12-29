from model.Ticker import get_ticker

########################################################################################################################

# data, indicators
asset = '6J'
num_months = 20
isNetwork = False

# strategy
enable_flips = False

# display
tick_size = str(get_ticker(asset).tick_size)
if 'e' in tick_size: trade_summary_decimals = int(tick_size[-1]) - 1 # scientific notation 5e-07
else: trade_summary_decimals = len(tick_size) - 2 # standard number, 1.25

########################################################################################################################
