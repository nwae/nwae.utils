
import os
import time as t
import datetime as dt
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


class LockFile:

    def __init__(self):
        return

    @staticmethod
    def acquire_file_cache_lock(
            lock_file_path,
            verbose = 0
    ):
        if lock_file_path is None:
            lg.Log.critical(str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                       + ': Lock file is None type, why obtain lock?!')
            return False

        count = 0
        sleep_time = 0.5
        max_count = 20
        while os.path.isfile(lock_file_path):
            lg.Log.important(str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                       + 'Waiting for file lock [' + lock_file_path + ']')
            t.sleep(sleep_time)
            count = count + 1
            if count >= max_count:
                lg.Log.critical(str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                + ': Cannot get file lock ['
                                + lock_file_path + '] after '
                                + str(sleep_time * max_count) + ' secs!!')
                return False

        try:
            f = open(file=lock_file_path, mode='w')
            timestamp = dt.datetime.fromtimestamp(t.time()).strftime('%Y-%m-%d %H:%M:%S')
            f.write(timestamp + '\n')
            f.close()
            return True
        except Exception as ex:
            lg.Log.critical(str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Unable to create lock file ['
                       + lock_file_path + ']: ' + str(ex))
            return False

    @staticmethod
    def release_file_cache_lock(
            lock_file_path,
            verbose = 0
    ):
        if lock_file_path is None:
            lg.Log.critical(str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Lock file is None type, why release lock?!')
            return False

        if not os.path.isfile(lock_file_path):
            lg.Log.critical(str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ' No lock file ['
                       + lock_file_path + '] to release!!')
            return True
        else:
            try:
                os.remove(lock_file_path)
                lg.Log.debug(str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                             + ': Lock file [' + lock_file_path + '] removed.')
                return True
            except Exception as ex:
                lg.Log.critical(str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                + ': Unable to remove lock file ['
                           + lock_file_path + ']: ' + str(ex))
                return False

