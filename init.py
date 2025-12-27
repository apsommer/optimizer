from model.Ticker import get_ticker

########################################################################################################################

# data, indicators
asset = '6J'
num_months = 30
isNetwork = False

# strategy
enable_flips = True

# display
trade_summary_decimals = len(str(get_ticker(asset))) - 2 # subtract '0.'

########################################################################################################################
