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
        case '6J': return Ticker('6J', 0.000001, 12.50)
    return None