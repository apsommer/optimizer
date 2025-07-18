from utils.utils import pretty_list


class LiveParams:

    def __init__(self,
        fastMinutes,
        disableEntryMinutes,
        fastMomentumMinutes,
        fastCrossoverPercent,
        takeProfitPercent,
        fastAngleFactor,
        slowMinutes,
        slowAngleFactor,
        coolOffMinutes,
        trendStartHour,
        trendEndHour):

        self.fastMinutes = fastMinutes
        self.disableEntryMinutes = disableEntryMinutes
        self.fastMomentumMinutes = fastMomentumMinutes
        self.fastCrossoverPercent = fastCrossoverPercent
        self.takeProfitPercent = takeProfitPercent
        self.fastAngleFactor = fastAngleFactor
        self.slowMinutes = slowMinutes
        self.slowAngleFactor = slowAngleFactor
        self.coolOffMinutes = coolOffMinutes
        self.trendStartHour = trendStartHour
        self.trendEndHour = trendEndHour

    @property
    def size(self):
        return (
            len(self.fastMinutes)
            * len(self.disableEntryMinutes)
            * len(self.fastMomentumMinutes)
            * len(self.fastCrossoverPercent)
            * len(self.takeProfitPercent)
            * len(self.fastAngleFactor)
            * len(self.slowMinutes)
            * len(self.slowAngleFactor)
            * len(self.coolOffMinutes)
            * len(self.trendStartHour)
            * len(self.trendEndHour))

    @property
    def one_line(self):
        return (f'['
            f'{self.fastMinutes}, '
            f'{self.disableEntryMinutes}, '
            f'{self.fastMomentumMinutes}, '
            f'{self.fastCrossoverPercent}, '
            f'{self.takeProfitPercent}, '
            f'{self.fastAngleFactor}, '
            f'{self.slowMinutes}, '
            f'{self.slowAngleFactor}, '
            f'{self.coolOffMinutes}, '
            f'{self.trendStartHour}, '
            f'{self.trendEndHour}]')

    def __repr__(self):

        if type(self.fastMinutes) == list:
            return(
                f'\n\t\tfastMinutes: {pretty_list(self.fastMinutes)}'
                f'\n\t\tdisableEntryMinutes: {pretty_list(self.disableEntryMinutes)}'
                f'\n\t\tfastMomentumMinutes: {pretty_list(self.fastMomentumMinutes)}'
                f'\n\t\tfastCrossoverPercent: {pretty_list(self.fastCrossoverPercent)}'
                f'\n\t\ttakeProfitPercent: {pretty_list(self.takeProfitPercent)}'
                f'\n\t\tfastAngleFactor: {pretty_list(self.fastAngleFactor)}'
                f'\n\t\tslowMinutes: {pretty_list(self.slowMinutes)}'
                f'\n\t\tslowAngleFactor: {pretty_list(self.slowAngleFactor)}'
                f'\n\t\tcoolOffMinutes: {pretty_list(self.coolOffMinutes)}'
                f'\n\t\ttrendStartHour: {pretty_list(self.trendStartHour)}'
                f'\n\t\ttrendEndHour: {pretty_list(self.trendEndHour)}'
            )

        return (
            f'\n\t\tfastMinutes: {self.fastMinutes}'
            f'\n\t\tdisableEntryMinutes: {self.disableEntryMinutes}'
            f'\n\t\tfastMomentumMinutes: {self.fastMomentumMinutes}'
            f'\n\t\tfastCrossoverPercent: {self.fastCrossoverPercent}'
            f'\n\t\ttakeProfitPercent: {self.takeProfitPercent}'
            f'\n\t\tfastAngleFactor: {self.fastAngleFactor}'
            f'\n\t\tslowMinutes: {self.slowMinutes}'
            f'\n\t\tslowAngleFactor: {self.slowAngleFactor}'
            f'\n\t\tcoolOffMinutes: {self.coolOffMinutes}'
            f'\n\t\ttrendStartHour: {self.trendStartHour}'
            f'\n\t\ttrendEndHour: {self.trendEndHour}'
        )
