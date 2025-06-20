class LiveParams:

    def __init__(self,
            fastMinutes,
            fastCrossoverPercent,
            takeProfitPercent,
            fastAngleFactor,
            slowMinutes,
            slowAngleFactor,
            coolOffMinutes,
            timeout):

        self.fastMinutes = fastMinutes
        self.fastCrossoverPercent = fastCrossoverPercent
        self.takeProfitPercent = takeProfitPercent
        self.fastAngleFactor = fastAngleFactor
        self.slowMinutes = slowMinutes
        self.slowAngleFactor = slowAngleFactor
        self.coolOffMinutes = coolOffMinutes
        self.timeout = timeout

    def __repr__(self):
        return (
            f'{self.fastMinutes}, {self.fastCrossoverPercent}, {self.takeProfitPercent}, {self.fastAngleFactor}, '
            f'{self.slowMinutes}, {self.slowAngleFactor}, {self.coolOffMinutes}, {self.timeout}')