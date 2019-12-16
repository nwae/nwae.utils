
import os
import time as t
import datetime as dt
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo
import threading
import random


class LockFile:

    __lock_mutex = threading.Lock()

    def __init__(self):
        return

    @staticmethod
    def __wait_for_lock_file(
            lock_file_path,
            max_wait_time_secs = 5.0
    ):
        total_sleep_time = 0.0

        while os.path.isfile(lock_file_path):
            lg.Log.important(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Waiting for file lock "' + str(lock_file_path)
                + '", ' + str(round(total_sleep_time,2)) + 's..'
            )
            sleep_time = random.uniform(0.1,0.5)
            t.sleep(sleep_time)
            total_sleep_time += sleep_time
            if total_sleep_time > max_wait_time_secs:
                lg.Log.critical(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Cannot get file lock "' + str(lock_file_path) + '" after '
                    + str(round(total_sleep_time,2)) + ' secs!!'
                )
                return False
        return True

    @staticmethod
    def acquire_file_cache_lock(
            lock_file_path,
            max_wait_time_secs = 5.0,
            verbose = 0
    ):
        if lock_file_path is None:
            lg.Log.critical(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Lock file is None type, why obtain lock?!'
            )
            return False

        if not LockFile.__wait_for_lock_file(
            lock_file_path = lock_file_path,
            max_wait_time_secs = max_wait_time_secs
        ):
            return False

        #
        # At this point there could be many competing processes waiting for it, so we
        # must do proper mutex locking.
        #
        try:
            LockFile.__lock_mutex.acquire()

            #
            # If many processes competing to obtain lock, make sure to check for file existence again
            # once a mutex is acquired. It is possible some other competing processes have obtained it.
            # So we wait a bit longer.
            #
            if not LockFile.__wait_for_lock_file(
                    lock_file_path = lock_file_path,
                    max_wait_time_secs = random.uniform(0.8,1.2)
            ):
                lg.Log.critical(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Failed to get lock. After obtaining mutex, other competing process won lock to file "'
                    + str(lock_file_path) + '"! Very likely process is being bombarded with too many requests.'
                )
                return False

            f = open(file=lock_file_path, mode='w')
            timestamp = dt.datetime.fromtimestamp(t.time()).strftime('%Y-%m-%d %H:%M:%S')
            f.write(timestamp + '\n')
            f.close()
            return True
        except Exception as ex:
            lg.Log.critical(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Unable to create lock file "' + str(lock_file_path) + '": ' + str(ex)
            )
            return False
        finally:
            LockFile.__lock_mutex.release()

    @staticmethod
    def release_file_cache_lock(
            lock_file_path,
            verbose = 0
    ):
        if lock_file_path is None:
            lg.Log.critical(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Lock file is None type, why release lock?!'
            )
            return False

        if not os.path.isfile(lock_file_path):
            lg.Log.critical(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ' No lock file "' + str(lock_file_path) + '" to release!!'
            )
            return True
        else:
            try:
                #
                # It is not possible for multiple processes to want to remove the lock
                # simultaneously since at any one time there should only be 1 process
                # having the lock.
                # So means there is no need to use mutexes.
                #
                os.remove(lock_file_path)
                lg.Log.debug(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Lock file "' + str(lock_file_path) + '" removed.'
                )
                return True
            except Exception as ex:
                lg.Log.critical(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Unable to remove lock file "' + str(lock_file_path) + '": ' + str(ex)
                )
                return False


if __name__ == '__main__':
    res = LockFile.acquire_file_cache_lock(
        lock_file_path = '/tmp/lockfile.test.lock',
        max_wait_time_secs = 2.2
    )
    print('Lock obtained = ' + str(res))
    res = LockFile.release_file_cache_lock(
        lock_file_path = '/tmp/lockfile.test.lock'
    )
    print('Lock released = ' + str(res))

    res = LockFile.acquire_file_cache_lock(
        lock_file_path = '/tmp/lockfile.test.lock',
        max_wait_time_secs = 2.2
    )
    print('Lock obtained = ' + str(res))
