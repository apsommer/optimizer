from analysis.Analyzer import Analyzer
from analysis.Engine import Engine
from model.Fitness import Fit
from strategy.LiveStrategy import LiveStrategy
from utils.metrics import *
from utils.utils import *

class WalkForward():

    def __init__(self, num_months, percent, runs, data, emas, fractals, opt, path):

        self.num_months = num_months
        self.percent = percent
        self.runs = runs
        self.data = data
        self.emas = emas
        self.fractals = fractals
        self.opt = opt
        self.path = path

        self.best_params = None
        self.best_fitness = None

        # calculate window sizes
        self.IS_len = round(len(data) / ((percent / 100) * runs + 1))
        self.OS_len = round((percent / 100) * self.IS_len)

        # init metrics
        self.metrics = init_walk_forward_metrics(self)

    def in_sample(self, run):

        # isolate in-sample training set
        IS_len = self.IS_len
        OS_len = self.OS_len
        IS_start = run * OS_len
        IS_end = IS_start + IS_len

        # mask dataset, one dataset each core
        IS_data = self.data.iloc[IS_start : IS_end]
        IS_emas = self.emas.iloc[IS_start : IS_end]
        IS_fractals = self.fractals.iloc[IS_start : IS_end]

        # run exhaustive sweep
        analyzer = Analyzer(run, IS_data, IS_emas, IS_fractals, self.opt, self.path)
        analyzer.run()
        analyzer.save()

    def out_of_sample(self, run):

        # isolate out-of-sample testing set
        IS_len = self.IS_len
        OS_len = self.OS_len
        IS_start = run * OS_len
        IS_end = IS_start + IS_len
        OS_start = IS_end
        OS_end = OS_start + OS_len

        # mask dataset, one dataset each core
        OS_data = self.data.iloc[OS_start : OS_end]
        OS_emas = self.emas.iloc[OS_start : OS_end]
        OS_fractals = self.fractals.iloc[OS_start : OS_end]

        # get fittest params from in-sample analyzer
        IS_path = self.path + '/' + str(run)
        fittest = unpack('analyzer', IS_path)['fittest']

        # todo skip extra fitness if only analyzing 1 engine

        # create and save engine for each fitness
        for fitness in tqdm(
            iterable = fittest,
            disable = run != 0, # show only 1 core
            colour = blue,
            bar_format = '        Out-of-sample:  {percentage:3.0f}%|{bar:100}{r_bar}'):

            # catch unprofitable in-sample
            metric = fittest[fitness]
            if metric is None: continue

            # extract params of fittest engine
            IS_engine = unpack(metric.id, IS_path)
            params = IS_engine['params']

            # run strategy blind with best params
            strategy = LiveStrategy(OS_data, OS_emas, OS_fractals, params)
            engine = Engine(
                id = run,
                strategy = strategy)
            engine.run()

            # capture in-sample profit for efficiency calculation
            IS_profit = next(metric.value for metric in IS_engine['metrics'] if metric.name == 'profit')
            metric = Metric('IS_profit', IS_profit, 'USD', 'In-sample profit', formatter = None, id = run)
            engine.metrics.append(metric)

            # persist full engine
            OS_path = self.path + '/' + fitness.value
            engine.save(OS_path, True)

    def build_composite(self, fitness):

        cash_series = pd.Series()
        trades = []
        IS_profits = []
        invalid_runs = []

        # stitch OS runs together
        for run in tqdm(
            iterable = range(self.runs),
            disable =fitness is not Fit.PROFIT, # show only 1 core
            colour = blue,
            bar_format = '        Composite:      {percentage:3.0f}%|{bar:100}{r_bar}'):

            # get cash balance at end of previous run
            if cash_series.empty: balance = initial_cash
            else: balance = cash_series.values[-1]

            # check if OS exists
            OS_path = self.path + '/' + fitness.value
            OS_engine_filepath = OS_path + '/' + str(run) + '.bin'
            isProfitable = os.path.exists(OS_engine_filepath)

            # OS exists: IS profitable
            if isProfitable:

                # extract saved OS engine results
                engine = unpack(run, OS_path)
                engine_cash_series = engine['cash_series']
                engine_trades = engine['trades']
                engine_metrics = engine['metrics']

                # capture in-sample profits for efficiency calculation
                metric = next(metric for metric in engine_metrics if metric.name == 'IS_profit')
                IS_profits.append(metric.value)

                # adjust series to starting balance
                engine_cash_series += balance - initial_cash

            # OS does not exist: IS not profitable
            else:

                # count invalid runs
                invalid_runs.append(run)

                # isolate testing set
                IS_len = self.IS_len
                OS_len = self.OS_len
                IS_start = run * OS_len
                IS_end = IS_start + IS_len
                OS_start = IS_end
                OS_end = OS_start + OS_len

                engine_cash_series = pd.Series(
                    index = self.data.index[OS_start : OS_end],
                    data = balance)

                engine_trades = []

            # cumulative cash series
            cash_series = pd.concat([cash_series, engine_cash_series], axis = 0)
            trades.extend(engine_trades)

        # reindex trades, 1-based for tradingview
        for i, trade in enumerate(trades): trade.id = i + 1

        # extract fittest engines from last in-sample analyzer
        IS_path = self.path + '/' + str(self.runs)
        fittest = unpack('analyzer', IS_path)['fittest']
        metric = fittest[fitness]

        # get params of fittest engine
        if metric is None: params = None
        else: params = unpack(str(metric.id), IS_path)['params']

        # mask indicators
        composite_data = self.data.loc[cash_series.index, :]
        composite_emas = self.emas.loc[cash_series.index, :]
        composite_fractals = self.fractals.loc[cash_series.index, :]

        # construct engine, but don't run!
        strategy = LiveStrategy(composite_data, composite_emas, composite_fractals, params)
        engine = Engine(fitness.value, strategy)
        engine.cash_series = cash_series
        engine.trades = trades
        engine.analyze()

        # calculate efficiency
        self.calculate_efficiency(IS_profits, engine)

        # capture number of invalid analyzers
        if len(invalid_runs) > 0:
            engine.metrics.append(
                Metric('invalids', str(invalid_runs), None, 'Invalid runs'))

        engine.save(self.path, True)

    def calculate_efficiency(self, IS_profits, engine):

        # in-sample annual return
        IS_total_profit = sum(IS_profits)
        IS_cash = IS_total_profit - initial_cash
        IS_days = self.OS_len * self.runs / 1440
        IS_annual_return = ((IS_cash / initial_cash) ** (1 / (IS_days / 365)) - 1) * 100

        # composite annual return
        metric = next(metric for metric in engine.metrics if metric.name == 'annual_return')
        engine_annual_return = metric.value

        efficiency = (engine_annual_return / IS_annual_return) * 100

        engine.metrics.append(
            Metric('efficiency', efficiency, '%', 'Efficiency'))

    def analyze(self):

        # isolate composite with highest profit
        highest_profit = -np.inf
        for fitness in Fit:

            engine = unpack(fitness.value, self.path)
            cash_series = engine['cash_series']
            cash = cash_series[-1]

            if cash > highest_profit:
                highest_profit = cash
                best_params = engine['params']
                best_fitness = fitness

        # persist results
        self.best_params = best_params
        self.best_fitness = best_fitness
        self.metrics += get_walk_forward_results_metrics(self)
        self.save()

    ''' serialize '''
    def save(self):

        bundle = {
            'best_params': self.best_params,
            'best_fitness': self.best_fitness,
            'metrics': self.metrics
        }

        save(
            bundle = bundle,
            filename = 'wfa',
            path = self.path)

    ####################################################################################################################

    def print_params_of_fittest_composite(self):

        for run in range(self.runs):

            # extract fittest engines from in-sample analyzer
            IS_path = self.path + '/' + str(run)
            fittest = unpack('analyzer', IS_path)['fittest']
            metric = fittest[self.best_fitness]

            # catch in-sample without profit
            if metric is None:
                print('\t' + str(run) + ': In-sample not profitable')
                continue

            # get params from fittest engine
            OS_engine = unpack(str(metric.id), IS_path)
            num_trades = next(metric.value for metric in OS_engine['metrics'] if metric.name == 'num_trades')
            params = OS_engine['params']

            # display to console
            print('\t' + str(run) + ', [' + str(metric.id) + '], (' + str(num_trades) + '): ' + params.one_line)

    def plot(self):

        ax = init_plot(
            window = 1,
            title = 'Equity')

        for fitness in Fit:

            # unpack composite engine
            composite = unpack(fitness.value, self.path)
            cash_series = composite['cash_series']

            # plot cash series
            fplt.plot(cash_series, color=fitness.color, legend=fitness.pretty, ax=ax)

            # consider composite with highest profit
            if fitness is self.best_fitness:

                # mask indicators
                start = cash_series.index[0]
                end = cash_series.index[-1]
                composite_data = self.data[start: end]
                composite_emas = self.emas[start: end]
                composite_fractals = self.fractals[start: end]

                # init engine
                params = composite['params']
                strategy = LiveStrategy(composite_data, composite_emas, composite_fractals, params)
                engine = Engine(fitness.value, strategy)

                # deserialize previous result
                engine.id = composite['id']
                engine.metrics = composite['metrics']
                engine.trades = composite['trades']
                engine.cash_series = cash_series
                engine.cash = cash_series[-1]

                # display results
                engine.print_metrics()
                engine.print_trades()
                engine.plot_trades()

                # plot initial cash
                fplt.plot(engine.initial_cash, color=dark_gray, ax=ax)

                # plot buy and hold
                size = engine.strategy.size
                point_value = engine.strategy.ticker.point_value
                # delta_df = composite.data.Close - composite.data.Close.iloc[0]
                delta_df = self.data.Close - self.data.Close.iloc[0]
                buy_hold = size * point_value * delta_df + initial_cash
                fplt.plot(buy_hold, color=dark_gray, ax=ax)

                # plot out-of-sample window boundaries
                for run in range(self.runs):

                    # isolate samples
                    IS_len = self.IS_len
                    OS_len = self.OS_len
                    IS_start = run * OS_len
                    IS_end = IS_start + IS_len
                    OS_start = IS_end

                    idx = self.data.index[OS_start]
                    fplt.add_line((idx, -1e6), (idx, 1e6), width = 1, style = '-', color = light_gray, ax = ax)

        fplt.show()