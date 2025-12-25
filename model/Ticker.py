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
        case 'MGC': return Ticker('MGC', 0.1, 1)
        case 'NG': return Ticker('NG', 0.001, 10)
        case '6E': return Ticker('6E', 0.00005, 6.25)
        case '6J': return Ticker('6J', 0.000001, 12.50)

    print(f'{symbol} not defined in get_ticker()')
    return None