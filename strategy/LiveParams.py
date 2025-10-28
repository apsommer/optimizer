import numpy
import numpy as np
from numpy import floating


class LiveParams:

    def __init__(self,
        fastMinutes,
        disableEntryMinutes,
        fastMomentumMinutes,
        fastCrossoverPercent,
        takeProfitPercent,
        stopLossPercent,
        fastAngleEntryFactor,
        fastAngleExitFactor,
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
        self.stopLossPercent = stopLossPercent
        self.fastAngleEntryFactor = fastAngleEntryFactor
        self.fastAngleExitFactor = fastAngleExitFactor
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
            * len(self.stopLossPercent)
            * len(self.fastAngleEntryFactor)
            * len(self.fastAngleExitFactor)
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
            f'{self.stopLossPercent}, '
            f'{self.fastAngleEntryFactor}, '
            f'{self.fastAngleExitFactor}, '
            f'{self.slowMinutes}, '
            f'{self.slowAngleFactor}, '
            f'{self.coolOffMinutes}, '
            f'{self.trendStartHour}, '
            f'{self.trendEndHour}]')

    def __repr__(self):

        if type(self.takeProfitPercent) == numpy.ndarray:
            return(
                f'\n\t\tfastMinutes: {pretty_list(self.fastMinutes)}'
                f'\n\t\tdisableEntryMinutes: {pretty_list(self.disableEntryMinutes)}'
                f'\n\t\tfastMomentumMinutes: {pretty_list(self.fastMomentumMinutes)}'
                f'\n\t\tfastCrossoverPercent: {pretty_list(self.fastCrossoverPercent)}'
                f'\n\t\ttakeProfitPercent: {pretty_list(self.takeProfitPercent)}'
                f'\n\t\tstopLossPercent: {pretty_list(self.stopLossPercent)}'
                f'\n\t\tfastAngleEntryFactor: {pretty_list(self.fastAngleEntryFactor)}'
                f'\n\t\tfastAngleExitFactor: {pretty_list(self.fastAngleExitFactor)}'
                f'\n\t\tslowMinutes: {pretty_list(self.slowMinutes)}'
                f'\n\t\tslowAngleFactor: {pretty_list(self.slowAngleFactor)}'
                f'\n\t\tcoolOffMinutes: {pretty_list(self.coolOffMinutes)}'
                f'\n\t\ttrendStartHour: {pretty_list(self.trendStartHour)}'
                f'\n\t\ttrendEndHour: {pretty_list(self.trendEndHour)}')

        return (
            f'\n\t\tfastMinutes: {self.fastMinutes}'
            f'\n\t\tdisableEntryMinutes: {self.disableEntryMinutes}'
            f'\n\t\tfastMomentumMinutes: {self.fastMomentumMinutes}'
            f'\n\t\tfastCrossoverPercent: {self.fastCrossoverPercent}'
            f'\n\t\ttakeProfitPercent: {self.takeProfitPercent}'
            f'\n\t\tstopLossPercent: {self.stopLossPercent}'
            f'\n\t\tfastAngleEntryFactor: {self.fastAngleEntryFactor}'
            f'\n\t\tfastAngleExitFactor: {self.fastAngleExitFactor}'
            f'\n\t\tslowMinutes: {self.slowMinutes}'
            f'\n\t\tslowAngleFactor: {self.slowAngleFactor}'
            f'\n\t\tcoolOffMinutes: {self.coolOffMinutes}'
            f'\n\t\ttrendStartHour: {self.trendStartHour}'
            f'\n\t\ttrendEndHour: {self.trendEndHour}')

def pretty_list(list):
    return (
        np.array2string(
            a = np.array(list),
            separator = ',',
            threshold = 3)
        .replace(' ', '')
        .replace(',', ', ')
        .replace('0.,', '0,'))
