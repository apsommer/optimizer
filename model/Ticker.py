class Ticker:

    def __init__(self, symbol, tick_size, tick_value):
        self.symbol = symbol
        self.tick_size = tick_size
        self.tick_value = tick_value

    def __repr__(self):
        return (
            f'\n\t\tsymbol: {self.symbol}'
            f'\n\t\ttick_size: {self.tick_size}'
            f'\n\t\ttick_value: {self.tick_value}'
        )

def get_ticker(symbol):

    match symbol:

        # Metals
        case 'MGC': return Ticker('MGC', 0.1, 1)
            # Silver, SIL (SI): 0.001, 1
            # Copper, MHG (HG): 0.0005, 1.25

        # Energy
        case 'NG': return Ticker('NG', 0.001, 10)
            # Oil, MCL: 0.01, 1 ... genetic pf too low

        # Currency
        case '6E': return Ticker('6E', 0.00005, 6.25)
        case '6J': return Ticker('6J', 0.0000005, 6.25)
            # 6B
            # 6A
            # 6C
            # 6S
            # Ether, MET (ETH): 0.05, 0.05 ... genetic pf too low
            # Bitcoin, MBT?

        # Agriculture
            # Corn, MZC (ZC): 0.005, 2.50 ... p&l too large

        # Interest rates
            # 10-year, MTN (ZN): 0.015625, 1.5625

        # US equities
        case 'ES': return Ticker('MES', 0.25, 1.25)
        case 'YM': return Ticker('MYM', 1.00, 0.50)
            # Nasdaq-100, Ticker('MNQ', 0.25, 0.50)
            # Russell-2000, M2K?

        # Global equities
            # Nikkei-225, MNK (NKD): 5, 2.50
            # DAX (FDAX / FDXM) – Germany
            # FTSE 100 (Z / L) – UK
            # Hang Seng (HSI / MHI) – Hong Kong
            # Euro Stoxx 50 (FESX) – Europe large caps

    print(f'{symbol} not defined in get_ticker()')
    return None