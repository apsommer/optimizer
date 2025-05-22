class Metric():
    def __init__(self):
        self.name = None
        self.value = None
        self.unit = None
        self.title = None
    def __repr__(self):
        return f'name: {self.name}, value: {self.value}, unit: {self.unit}, title: {self.title}'