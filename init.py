from model.Ticker import get_ticker_decimals

########################################################################################################################

# data, indicators
asset = 'NG'
num_months = 20
isNetwork = False

# strategy
enable_flips = True

########################################################################################################################

# trade display in console
decimals = get_ticker_decimals(asset)
