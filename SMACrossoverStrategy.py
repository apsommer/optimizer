from BaselineStrategy import BaselineStrategy

class SMACrossoverStrategy(BaselineStrategy):

    def __init__(self):
        super().__init__()
        self.order_size = 1

    def on_bar(self):

        if (self.position_size == 0 and
                self.data.loc[self.current_idx].sma_12 > self.data.loc[self.current_idx].sma_24):
            self.buy('long', size=self.order_size)
            # print('long @ ' + str(self.current_idx))

        elif (self.position_size == 1 and
              self.data.loc[self.current_idx].sma_12 < self.data.loc[self.current_idx].sma_24):
            self.sell('close long', size=self.position_size)
            # print('close long @ ' + str(self.current_idx))