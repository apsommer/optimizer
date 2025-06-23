class FastParams:

    def __init__(self,
        takeProfitPercent,
        stopLossPercent,
        proximityPercent,
    ):

        self.takeProfitPercent = takeProfitPercent
        self.stopLossPercent = stopLossPercent
        self.slowAngleFactor = proximityPercent

    def __repr__(self):
        return (
            f'{self.takeProfitPercent}, {self.stopLossPercent}, {self.slowAngleFactor}')

