class Metric():
    def __init__(self, name, value, unit, title):
        self.name = name
        self.value = value
        self.unit = unit
        self.title = title
    def __repr__(self):
        return f'name: {self.name}, value: {self.value}, unit: {self.unit}, title: {self.title}'