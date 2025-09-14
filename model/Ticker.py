class Ticker:

    def __init__(self, symbol, tick_size, tick_value, margin):
        self.symbol = symbol
        self.tick_size = tick_size
        self.tick_value = tick_value
        self.margin = margin

    def __repr__(self):
        return (
            f'\n\t\tsymbol: {self.symbol}'
            f'\n\t\ttick_size: {self.tick_size}'
            f'\n\t\ttick_value: {self.tick_value}'
            f'\n\t\tmargin: {self.margin}')