class FastParams:

    def __init__(self,
         takeProfitPercent,
         stopLossRatio,
         slowAngleFactor,
         stopAverage
         ):

        self.takeProfitPercent = takeProfitPercent
        self.stopLossRatio = stopLossRatio
        self.slowAngleFactor = slowAngleFactor
        self.stopAverage = stopAverage

    def __repr__(self):
        return (
            f'{self.takeProfitPercent}, {self.stopLossRatio}, {self.slowAngleFactor}, {self.stopAverage}')

