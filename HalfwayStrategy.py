from BaselineStrategy import BaselineStrategy

class HalfwayStrategy(BaselineStrategy):

    def __init__(self):
        super().__init__()

        self.barIndex = None
        self.order_size = 1

    def init(self):
        self.barIndex = -1

    def on_bar(self):

        self.barIndex += 1
        barIndex = self.barIndex

        open = self.data.Open
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        is_long = self.position_size > 0
        is_short = 0 > self.position_size



        ################################################################################################################

        if (self.position_size == 0 and
                self.data.loc[self.current_idx].sma_12 > self.data.loc[self.current_idx].sma_24):
            self.buy('long', size=self.order_size)
            # print('long @ ' + str(self.current_idx))

        elif (self.position_size == 1 and
              self.data.loc[self.current_idx].sma_12 < self.data.loc[self.current_idx].sma_24):
            self.sell('close long', size=self.position_size)
            # print('close long @ ' + str(self.current_idx))