class Ticker:
    def __init__(self, symbol, tick_size, point_value, margin):
        self.symbol = symbol
        self.tick_size = tick_size
        self.point_value = point_value
        self.margin_requirement = margin

    def __repr__(self):
        return f'\n\t\tsymbol: {self.symbol}\n\t\ttick_size: {self.tick_size}\n\t\tpoint_value: {self.point_value}\n\t\tmargin_requirement: {self.margin_requirement}'