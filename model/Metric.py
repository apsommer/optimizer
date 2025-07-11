class Metric():
    def __init__(self, name, value, unit, title, formatter=None, id=None):
        self.name = name
        self.value = value
        self.unit = unit
        self.title = title
        self.formatter = formatter
        self.id = id

    def __repr__(self):
        return (
            f'name: {self.name}, '
            f'value: {self.value},'
            f'unit: {self.unit},'
            f'title: {self.title},'
            f'formatter: {self.formatter},'
            f'id: {self.id}')