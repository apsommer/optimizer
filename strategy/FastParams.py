class FastParams:

    def __init__(self,
        takeProfitPercent,
        slowAngleFactor,
        stopAverage
    ):

        self.takeProfitPercent = takeProfitPercent
        self.slowAngleFactor = slowAngleFactor
        self.stopAverage = stopAverage

    def __repr__(self):
        return (
            f'{self.takeProfitPercent}, {self.slowAngleFactor}, {self.stopAverage}')

