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
            f'\n\t\ttakeProfitPercent: {self.takeProfitPercent}\n\t\tstopLossRatio: {self.stopLossRatio}\n\t\tslowAngleFactor: {self.slowAngleFactor}\n\t\tstopAverage: {self.stopAverage}')

