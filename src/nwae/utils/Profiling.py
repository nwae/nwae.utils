
import datetime
import time
import numpy as np
from inspect import getframeinfo, currentframe
from nwae.utils.Log import Log
import threading


class Profiling:

    def __init__(self):
        return

    @staticmethod
    def start():
        return datetime.datetime.now()

    @staticmethod
    def stop():
        return datetime.datetime.now()

    @staticmethod
    def get_time_dif_secs(
            start,
            stop,
            decimals=4
    ):
        diftime = (stop - start)
        diftime = round(diftime.days*86400 + diftime.seconds + diftime.microseconds / 1000000, decimals)
        return diftime

    @staticmethod
    def get_time_dif(
            start,
            stop,
            decimals=4
    ):
        return Profiling.get_time_dif_secs(
            start = start,
            stop  = stop,
            decimals = decimals
        )

    @staticmethod
    def get_time_dif_str(
            start,
            stop,
            decimals=4
    ):
        return (str(Profiling.get_time_dif(start, stop, decimals)) + ' secs')


class ProfilingHelper:

    ALGORITHM_STANDARD = 'standard'
    ALGORITHM_EMA = 'ema'

    EMA_ALPHA = 1/100

    def __init__(
            self,
            profiler_name,
            # EMA будет быстрее
            algorithm = ALGORITHM_STANDARD,
            # Applies for standard algorithm only
            max_list_len = 1000
    ):
        self.profiler_name = profiler_name
        self.algorithm = algorithm
        self.max_list_len = max_list_len

        self.profiler_times = np.array([], dtype=float)
        self.ema = None
        self.running_average = None
        self.running_median = None
        self.__mutex = threading.Lock()
        return

    def profile_time(self, start_time, additional_info=''):
        total_time = Profiling.get_time_dif_secs(start=start_time, stop=Profiling.stop(), decimals=5)
        self.__mutex.acquire()
        try:
            self.profiler_times = np.append(self.profiler_times, [total_time])
            if self.algorithm == self.ALGORITHM_STANDARD:
                l = len(self.profiler_times)
                self.running_median = np.round(np.median(self.profiler_times), 5)
                self.running_average = np.round(np.average(self.profiler_times), 5)
                if l > self.max_list_len:
                    self.profiler_times = self.profiler_times[1:l]
            elif self.algorithm == self.ALGORITHM_EMA:
                if self.ema is None:
                    self.ema = total_time
                self.ema = ( (1-self.EMA_ALPHA) * self.ema ) + ( self.EMA_ALPHA * total_time )
                self.ema = np.round(self.ema, 5)
                l = None
                self.running_median = None
                self.running_average = self.ema
            else:
                raise Exception('Not implemented algorithm "' + str(self.algorithm) + '"')
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Profiling "' + str(self.profiler_name)  + ' ' + str(additional_info)
                + '" took ' + str(total_time) + 's, running average '
                + str(self.running_average) + 's, running median = ' + str(self.running_median)
                + 's (total len=' + str(l) + ')'
            )
            # print(self.profiler_times)
        finally:
            self.__mutex.release()


if __name__ == '__main__':

    a = Profiling.start()
    time.sleep(2.59384)
    b = Profiling.stop()

    print(Profiling.get_time_dif(a, b))
    print(Profiling.get_time_dif_secs(a, b))

    Log.DEBUG_PRINT_ALL_TO_SCREEN = True
    Log.LOGLEVEL = Log.LOG_LEVEL_IMPORTANT
    for algo in [ProfilingHelper.ALGORITHM_STANDARD, ProfilingHelper.ALGORITHM_EMA]:
        p = ProfilingHelper(profiler_name='test ' + str(algo), algorithm=algo)
        start_time = datetime.datetime.now()
        for i in range(5000):
            p.profile_time(start_time=start_time)
        print(
            'Algo "' + str(algo) + '" took '
            + str(Profiling.get_time_dif_secs(start=start_time, stop=Profiling.stop())) + 's'
        )
        print('Final average = ' + str(p.running_average) + ', median = ' + str(p.running_median))

