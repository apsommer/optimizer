class LiveParams:
    def __init__(
            self,
            fastMinutes,
            disableEntryMinutes,
            fastMomentumMinutes,
            fastCrossoverPercent,
            takeProfitPercent,
            fastAngleFactor,
            slowMinutes,
            slowAngleFactor,
            coolOffMinutes = 5,
            positionEntryMinutes = 1):

        self.fastMinutes = fastMinutes
        self.disableEntryMinutes = disableEntryMinutes
        self.fastMomentumMinutes = fastMomentumMinutes
        self.fastCrossoverPercent = fastCrossoverPercent
        self.takeProfitPercent = takeProfitPercent
        self.fastAngleFactor = fastAngleFactor
        self.slowMinutes = slowMinutes
        self.slowAngleFactor = slowAngleFactor
        self.coolOffMinutes = coolOffMinutes
        self.positionEntryMinutes = positionEntryMinutes
