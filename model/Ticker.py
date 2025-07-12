class Ticker:
    def __init__(self, symbol, tick_size, point_value, margin):
        self.symbol = symbol
        self.tick_size = tick_size
        self.point_value = point_value
        self.margin = margin

    def __repr__(self):
        return (
            f'\n\t\tsymbol: {self.symbol}'
            f'\n\t\t'f'tick_size: {self.tick_size}'
            f'\n\t\tpoint_value: {self.point_value}'
            f'\n\t\tmargin: {self.margin}')