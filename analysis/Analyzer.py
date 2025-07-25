from analysis.Engine import Engine
from model.Fitness import Fit
from strategy.LiveParams import LiveParams
from strategy.LiveStrategy import *
from utils.metrics import *
from utils.utils import *

class Analyzer:

    def __init__(self, id, data, emas, fractals, opt, wfa_path):

        self.id = id
        self.data = data
        self.emas = emas
        self.fractals = fractals
        self.opt = opt
        self.wfa_path = wfa_path

        self.path = wfa_path  + '/' + str(id) + '/'
        self.engine_metrics = []
        self.metrics = []
        self.fittest = { }

        # extract optimization params
        self.fastMinutes = self.opt.fastMinutes
        self.disableEntryMinutes = self.opt.disableEntryMinutes
        self.fastMomentumMinutes = self.opt.fastMomentumMinutes
        self.fastCrossoverPercent = self.opt.fastCrossoverPercent
        self.takeProfitPercent = self.opt.takeProfitPercent
        self.fastAngleFactor = self.opt.fastAngleFactor
        self.slowMinutes = self.opt.slowMinutes
        self.slowAngleFactor = self.opt.slowAngleFactor
        self.coolOffMinutes = self.opt.coolOffMinutes
        self.trendStartHour = self.opt.trendStartHour
        self.trendEndHour = self.opt.trendEndHour

    def run(self):

        # todo pass cores instead
        isFirstProcess = '0' == multiprocessing.current_process().name

        id = 0
        with tqdm(
            disable = self.id != 0, # show only 1 core
            total = self.opt.size,
            colour = blue,
            bar_format = '        In-sample:      {percentage:3.0f}%|{bar:100}{r_bar}') as pbar:

            # sweep params from opt
            for fastMinutes in self.fastMinutes:
                for disableEntryMinutes in self.disableEntryMinutes:
                    for fastMomentumMinutes in self.fastMomentumMinutes:
                        for fastCrossoverPercent in self.fastCrossoverPercent:
                            for takeProfitPercent in self.takeProfitPercent:
                                for fastAngleFactor in self.fastAngleFactor:
                                    for slowMinutes in self.slowMinutes:
                                        for slowAngleFactor in self.slowAngleFactor:
                                            for coolOffMinutes in self.coolOffMinutes:
                                                for trendStartHour in self.trendStartHour:
                                                    for trendEndHour in self.trendEndHour:

                                                        # update params
                                                        params = LiveParams(
                                                            fastMinutes = fastMinutes,
                                                            disableEntryMinutes = disableEntryMinutes,
                                                            fastMomentumMinutes = fastMomentumMinutes,
                                                            fastCrossoverPercent = fastCrossoverPercent,
                                                            takeProfitPercent = takeProfitPercent,
                                                            fastAngleFactor = fastAngleFactor,
                                                            slowMinutes = slowMinutes,
                                                            slowAngleFactor = slowAngleFactor,
                                                            coolOffMinutes = coolOffMinutes,
                                                            trendStartHour = trendStartHour,
                                                            trendEndHour = trendEndHour)

                                                        # init strategy and engine
                                                        strategy = LiveStrategy(self.data, self.emas, self.fractals, params)
                                                        engine = Engine(id, strategy)

                                                        # run and save
                                                        engine.run(disable = not isFirstProcess)
                                                        engine.save(self.path, False)

                                                        id += 1
                                                        pbar.update()

        pbar.close()
        self.analyze()

    def analyze(self):

        # get num of files in dir
        num_engines = len(os.listdir(self.path))
        ids = np.arange(0, num_engines, 1)

        # collect engine metrics
        for id in ids:

            engine_metrics = unpack(id, self.path)['metrics']

            # filter out engines with loss
            profit = next(metric.value for metric in engine_metrics if metric.name == 'profit')
            if 0 > profit: continue

            self.engine_metrics.extend(engine_metrics)

        # init analyzer metrics
        self.metrics = get_analyzer_metrics(self)

        # collect fittest engines
        for fitness in Fit:

            # get fittest engine
            metric = self.get_fittest_metric(fitness)
            self.fittest[fitness] = metric

            # skip adding to analyzer metrics if not profitable
            if metric is None: continue
            self.metrics.append(metric)

    def get_fittest_metric(self, fitness):

        # isolate fitness metrics
        fitness_metrics = []
        for metric in self.engine_metrics:
            if metric.name == fitness.value:
                fitness_metrics.append(metric)

        # catch no profitable engines for this fitness
        if len(fitness_metrics) == 0:
            return None

        # sort by value
        fitness_metrics = sorted(
            fitness_metrics,
            key = lambda it: it.value,
            reverse = True)

        # tag title
        metric = fitness_metrics[0]
        metric.title = f'[{metric.id}] {metric.title}'
        return metric

    def save(self):

        save(
            bundle = {
                'id': self.id,
                'metrics': self.metrics,
                'fittest': self.fittest,
            },
            filename = 'analyzer',
            path = self.path)
