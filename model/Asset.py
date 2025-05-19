class Ticker:
    def __init__(self, symbol, tick_value):
        self.symbol = symbol
        self.tick_value = tick_value

    def __repr__(self):
        return f'\n\t\tsymbol: {self.symbol}\n\t\ttick_value: {self.tick_value}'