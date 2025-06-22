class FastParams:

    def __init__(self,
        takeProfitPercent,
        stopLossPercent,
    ):

        self.takeProfitPercent = takeProfitPercent
        self.stopLossPercent = stopLossPercent

    def __repr__(self):
        return (
            f'{self.takeProfitPercent}, {self.stopLossPercent}')

