# -*- coding: utf-8 -*-
import signal
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe


class SignalHandler:
    kill_now = False

    def __init__(
            self,
            # Your own exit callback function
            exit_callback,
            signals_list = (signal.SIGINT, signal.SIGTERM)
    ):
        self.exit_callback = exit_callback
        self.signals_list = signals_list
        for sg in self.signals_list:
            signal.signal(sg, self.exit_gracefully)

    def exit_gracefully(
            self,
            signum,
            frame
    ):
        Log.critical(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Signal ' + str(signum) + ' received.'
        )
        self.exit_callback()
        return


if __name__ == '__main__':
    class ExitClass:
        def __init__(self):
            self.done = False

        def exit_func(self):
            self.done = True

    ec = ExitClass()
    sh = SignalHandler(exit_callback=ec.exit_func)

    i = 1
    while True:
        if ec.done:
            break
        print(i)
        i += 1
        import time
        time.sleep(1)
    exit(0)
