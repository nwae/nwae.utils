# -*- coding: utf-8 -*-

import threading
import queue as q
import time
import nwae.utils.Log as lg
from inspect import getframeinfo, currentframe
import nwae.utils.StringUtils as su


#
# Puts threads to a single group, so we can start/kill everything together
#
class ThreadGroup(threading.Thread):

    def __init__(
            self,
            thread_group_name
    ):
        super(ThreadGroup, self).__init__()
        self.thread_group_name = thread_group_name
        self.thread_collection = {}
        return

    #
    # Returns True of False, if successful or not
    #
    def add_thread(
            self,
            new_thread_name,
            new_thread
    ):
        # if type(new_thread) is not threading.Thread:
        #     errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
        #              + ': [' + str(self.thread_group_name) + '] New thread "' + str(new_thread_name)\
        #              + '" not correct type, instead of type "' + str(type(new_thread)) + '".'
        #     lg.Log.error(errmsg)
        #     raise Exception(errmsg)

        key = su.StringUtils.trim(str(new_thread_name))
        # If existing thread of the same name exists
        if key == '':
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': [' + str(self.thread_group_name) + '] Thread name must not be empty!'
            lg.Log.warning(errmsg)
            return False

        if key in self.thread_collection.keys():
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': [' + str(self.thread_group_name) + '] Thread "' + str(new_thread_name)\
                     + '" already exists in collection!'
            lg.Log.warning(errmsg)
            return False

        self.thread_collection[key] = new_thread
        return True

    def start_thread_group(
            self
    ):
        for th_name in self.thread_collection.keys():
            th = self.thread_collection[th_name]
            lg.Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                + ': [' + str(self.thread_group_name) + '] Starting thread "' + str(th_name) + '"..'
            )
            th.start()

    def run(self):
        sleep_while = 2
        lg.Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': [' + str(self.thread_group_name) + '] Starting thread group..'
        )
        is_any_thread_dead = False
        while True:
            if is_any_thread_dead:
                # Kill all threads
                for th_name in self.thread_collection.keys():
                    th = self.thread_collection[th_name]
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                        + ': [' + str(self.thread_group_name) + '] Joining Thread "' + str(th_name) + '"..'
                    )
                    th.join()
                lg.Log.info(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': All threads of thread group "' + str(self.thread_group_name)  + '" joined..'
                )
                break

            for th_name in self.thread_collection.keys():
                th = self.thread_collection[th_name]
                if not th.isAlive():
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                        + ': [' + str(self.thread_group_name) + '] Thread "' + str(th_name)
                        + '" no longer alive. Killing everyone else.'
                    )
                    is_any_thread_dead = True
                    break

                if not is_any_thread_dead:
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                        + ': [' + str(self.thread_group_name) + '] All threads OK.'
                    )
            time.sleep(sleep_while)


if __name__ == '__main__':
    class TaskThread(threading.Thread):
        def __init__(self, thread_name, sleep_time):
            super(TaskThread, self).__init__()
            self.thread_name = thread_name
            self.sleep_time = sleep_time
            self.stoprequest = threading.Event()

        def join(self, timeout=None):
            print('Thread ' + self.thread_name + ' join called.')
            self.stoprequest.set()
            super(TaskThread, self).join(timeout=timeout)
            return

        def run(self):
            # Break sleep into small pieces
            quantum = 2
            count = 0
            run_quantized_sleeps = True
            while True:
                if self.stoprequest.isSet():
                    print('Thread ' + self.thread_name + ' stop request received..')
                    break
                # Task is to sleep
                if run_quantized_sleeps:
                    time.sleep(quantum)
                    count = count+1
                    if count*quantum > self.sleep_time:
                        break
                else:
                    time.sleep(self.sleep_time)
            print('Sleep done for thread "' + str(self.thread_name) + '"..')

    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_INFO

    #
    # We demo starting t1 thread whose job is to sleep for 5 secs.
    # t2 and t3 has a harder job to sleep for 500/800 secs.
    # However when the the tg thread group detects that t1 is dead,
    # its job is to kill t2 and t3.
    #
    t1 = TaskThread(thread_name='t1', sleep_time=5)
    t2 = TaskThread(thread_name='t2', sleep_time=500)
    t3 = TaskThread(thread_name='t3', sleep_time=800)

    tg = ThreadGroup(thread_group_name='tg')
    tg.add_thread(new_thread_name=t1.thread_name, new_thread=t1)
    tg.add_thread(new_thread_name=t2.thread_name, new_thread=t2)
    tg.add_thread(new_thread_name=t3.thread_name, new_thread=t3)

    tg.start_thread_group()
    tg.start()

    exit(0)
