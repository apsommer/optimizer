from model.Trade import Trade
from utils.metrics import *
from utils.utils import *

class Engine:

    def __init__(self, id, strategy):

        self.id = id
        self.strategy = strategy

        self.data = strategy.data
        self.current_idx = -1
        self.trades = []
        self.metrics = []
        self.cash_series = pd.Series(index = self.data.index)
        self.initial_cash = initial_cash
        self.cash = self.initial_cash

    def run(self):

        # progress bar attributes
        isFirstProcess = '0' == multiprocessing.current_process().name

        for idx in tqdm(
            disable = not isFirstProcess,
            leave = False,
            position = 2, # todo pass as arg, wfa = 1, genetic = 2
            iterable = self.data.index,
            colour = aqua,
            bar_format = '                        {percentage:3.0f}%|{bar:100}{r_bar}'):

            # set index
            self.current_idx = idx
            self.strategy.current_idx = self.current_idx

            # execute strat
            self.strategy.on_bar()

            # fill orders, if needed
            orders = self.strategy.orders
            if len(orders) > 0 and orders[-1].idx == self.current_idx:
                self.fill_orders()

            # track cash balance
            self.cash_series[idx] = self.cash

        # analyze results
        self.analyze()

    def fill_orders(self):

        # consider last order and trade
        order = self.strategy.orders[-1]
        if len(self.trades) == 0: trade = None
        else: trade = self.trades[-1]

        # enter new trade
        if trade is None or trade.is_closed:
            self.trades.append(
                Trade(
                    id = len(self.trades) + 1,
                    side = order.sentiment,
                    size = order.size,
                    entry_order = order,
                    exit_order = None))
            return

        # close open trade
        trade.exit_order = order
        self.cash += trade.profit

        # flip, enter new trade immediately on exit
        if 'flip' in order.comment:
            entry_order = self.strategy.orders[-2]
            self.trades.append(
                Trade(
                    id = len(self.trades) + 1,
                    side = entry_order.sentiment,
                    size = entry_order.size,
                    entry_order = entry_order,
                    exit_order = None))

    def analyze(self):

        # build metrics
        self.metrics = get_engine_metrics(self)

        # tag all metrics with engine id
        for metric in self.metrics: metric.id = self.id

    ''' serialize '''
    def save(self, path, isFull):

        # out-of-sample
        if isFull: bundle = {
            'id': self.id,
            'params': self.strategy.params,
            'metrics': self.metrics,
            'trades': self.trades,
            'cash_series': self.cash_series
        }

        # in-sample
        else: bundle = {
            'id': self.id,
            'params': self.strategy.params,
            'metrics': self.metrics
        }

        save(
            bundle = bundle,
            filename = str(self.id),
            path = path)

    ####################################################################################################################

    def print_metrics(self):
        print_metrics(self.metrics)

    def print_trades(self):

        show_last = 3
        trades = self.trades

        # header
        print('\nTrades:')
        print('\t\t\t\t\tclose\tprofit\tcomment')
        if len(trades) > show_last: print('\t...')

        # trades
        for trade in trades[-show_last:]: print(trade)
        print()

    def plot_trades(self, shouldShow = False):

        # init
        ax = self.strategy.plot(
            window = 0,
            title = f'Engine: {self.id}')

        # candlesticks
        data = self.data
        fplt.candlestick_ochl(
            data[['Open', 'Close', 'High', 'Low']],
            ax = ax)

        # init dataframe of plot entities
        entities = pd.DataFrame(
            index = data.index,
            dtype = float,
            columns = [
                'long_entry',
                'short_entry',
                'profit_exit',
                'loss_exit'])

        for trade in self.trades:

            # entry
            entry_idx = trade.entry_order.idx
            entry_price = trade.entry_order.price
            if trade.is_long: entities.loc[entry_idx, 'long_entry'] = entry_price
            else: entities.loc[entry_idx, 'short_entry'] = entry_price

            # exit
            exit_idx = trade.exit_order.idx
            exit_price = trade.exit_order.price
            profit = trade.profit
            if profit > 0:
                entities.loc[exit_idx, 'profit_exit'] = exit_price
                entities.loc[exit_idx, 'loss_exit'] = np.nan
            else:
                entities.loc[exit_idx, 'profit_exit'] = np.nan
                entities.loc[exit_idx, 'loss_exit'] = exit_price

            # trade line
            color = blue
            if trade.is_short: color = aqua

            fplt.add_line(
                p0 = (entry_idx, entry_price),
                p1 = (exit_idx, exit_price),
                color = color,
                width = 7,
                ax = ax)

        # exits
        fplt.plot(entities['profit_exit'], style='o', width = 3, color=green, ax=ax)
        fplt.plot(entities['loss_exit'], style='o', width = 3, color=red, ax=ax)

        if shouldShow: fplt.show()

    def plot_equity(self):

        ax = init_plot(
            window = 1,
            title = f'{self.id}: Equity')

        # reference buy and hold
        size = self.strategy.size
        point_value = self.strategy.ticker.point_value
        delta_df = self.data.Close - self.data.Close.iloc[0]
        buy_hold = size * point_value * delta_df + self.initial_cash
        fplt.plot(buy_hold, color=dark_gray, ax=ax)

        # initial cash
        fplt.add_line(
            p0 = (self.data.index[0], initial_cash),
            p1 = (self.data.index[-1], initial_cash),
            color = dark_gray,
            ax = ax)

        # equity
        fplt.plot(self.cash_series, ax = ax)
        fplt.show()