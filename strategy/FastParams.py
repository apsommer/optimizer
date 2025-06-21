class FastParams:

    def __init__(self,
        takeProfitPercent,
        num
    ):

        self.takeProfitPercent = takeProfitPercent
        self.num = num

    def __repr__(self):
        return (
            f'{self.takeProfitPercent}, {self.num}')