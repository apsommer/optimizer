class FastParams:

    def __init__(self,
        takeProfitPercent,
        stopLossPercent,
        proximityPercent,
    ):

        self.takeProfitPercent = takeProfitPercent
        self.stopLossRatio = stopLossPercent
        self.slowAngleFactor = proximityPercent

    def __repr__(self):
        return (
            f'{self.takeProfitPercent}, {self.stopLossRatio}, {self.slowAngleFactor}')

