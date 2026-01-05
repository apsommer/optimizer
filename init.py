from model.Ticker import get_ticker_decimals

########################################################################################################################

# data, indicators
asset = 'ES'
num_months = 20
isNetwork = False

# strategy
enable_flips = False

########################################################################################################################

# trade display in console
decimals = get_ticker_decimals(asset)
