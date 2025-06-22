class FastParams:

    def __init__(self,
        takeProfitPercent,
        stopLossPercent,
        num
    ):

        self.takeProfitPercent = takeProfitPercent
        self.stopLossPercent = stopLossPercent
        self.num = num

    def __repr__(self):
        return (
            f'{self.takeProfitPercent}, {self.stopLossPercent}, {self.num}')