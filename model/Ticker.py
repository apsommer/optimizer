class Ticker:
    def __init__(self, symbol, tick_value, margin_requirement):
        self.symbol = symbol
        self.tick_value = tick_value
        self.margin_requirement = margin_requirement

    def __repr__(self):
        return f'\n\t\tsymbol: {self.symbol}\n\t\ttick_value: {self.tick_value}\n\t\tmargin_requirement: {self.margin_requirement}'