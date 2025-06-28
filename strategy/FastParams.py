class FastParams:

    def __init__(self,
        takeProfitPercent,
        stopLossRatio,
        slowAngleFactor,
        stopAverage,
        restrictionMinutes,
    ):

        self.takeProfitPercent = takeProfitPercent
        self.stopLossRatio = stopLossRatio
        self.slowAngleFactor = slowAngleFactor
        self.stopAverage = stopAverage
        self.restrictionMinutes = restrictionMinutes

    def __repr__(self):
        return (
            f'\n\t\ttakeProfitPercent: {self.takeProfitPercent}'
            f'\n\t\tstopLossRatio: {self.stopLossRatio}'
            f'\n\t\tslowAngleFactor: {self.slowAngleFactor}'
            f'\n\t\tstopAverage: {self.stopAverage}'
            f'\n\t\trestrictionMinutes: {self.restrictionMinutes}'
        )

