
import datetime
import time


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


if __name__ == '__main__':

    a = Profiling.start()
    time.sleep(2.59384)
    b = Profiling.stop()

    print(Profiling.get_time_dif(a, b))
    print(Profiling.get_time_dif_str(a, b))
