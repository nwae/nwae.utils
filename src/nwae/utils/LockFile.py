
import os
import time as t
import datetime as dt
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo
import threading
import random
import uuid


class LockFile:

    N_RACE_CONDITIONS_MEMORY = 0
    N_RACE_CONDITIONS_FILE = 0

    LOCKS_DICT = {}

    def __init__(self):
        return

    @staticmethod
    def __wait_for_lock_file(
            lock_file_path,
            max_wait_time_secs
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
                lg.Log.warning(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Wait fail for file lock "' + str(lock_file_path) + '" after '
                    + str(round(total_sleep_time,2)) + ' secs!!'
                )
                return False
        return True

    @staticmethod
    def acquire_file_cache_lock(
            lock_file_path,
            max_wait_time_secs = 30.0,
            verbose = 0
    ):
        if lock_file_path is None:
            lg.Log.critical(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Lock file is None type, why obtain lock?!'
            )
            return False

        #
        # At this point there could be many competing workers/threads waiting for it.
        # And since they can be cross process, means no point using any mutex locks.
        #
        wait_time_per_round = 0.5
        lg.Log.debugdebug(
            str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Wait time per round ' + str(round(wait_time_per_round,2))
        )
        random_val = wait_time_per_round / 10
        total_wait_time = 0
        round_count = 0
        while True:
            round_count += 1
            if total_wait_time > max_wait_time_secs:
                lg.Log.critical(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Round ' + str(round_count)
                    + '. Failed to get lock ~' + str(total_wait_time) + 's. Other competing process won lock to file "'
                    + str(lock_file_path) + '"! Very likely process is being bombarded with too many requests.'
                )
                return False

            # Rough estimation without the random value
            total_wait_time += wait_time_per_round

            if not LockFile.__wait_for_lock_file(
                    lock_file_path = lock_file_path,
                    max_wait_time_secs = random.uniform(
                        wait_time_per_round-random_val,
                        wait_time_per_round+random_val
                    )
            ):
                lg.Log.important(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Round ' + str(round_count) + ' fail to get lock to file "'
                    + str(lock_file_path) + '".'
                )
                continue
            else:
                lg.Log.debugdebug('Lock file "' + str(lock_file_path) + '" ok, no longer found.')

            #
            # We use additional memory lock for race conditions
            #
            if lock_file_path in LockFile.LOCKS_DICT.keys():
                LockFile.N_RACE_CONDITIONS_MEMORY += 1
                lg.Log.warning(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Memory Race condition ' + str(LockFile.N_RACE_CONDITIONS_MEMORY)
                    + '! Round ' + str(round_count)
                    + '. Lock file "' + str(lock_file_path) + '" in memory lock.'
                )
                continue
            else:
                LockFile.LOCKS_DICT[lock_file_path] = 1

            try:
                f = open(file=lock_file_path, mode='w')
                timestamp = dt.datetime.now()
                random_string = uuid.uuid4().hex + ' ' + str(timestamp) + ' ' + str(threading.get_ident())
                f.write(random_string)
                f.close()
                # Should be 2 now
                LockFile.LOCKS_DICT[lock_file_path] += 1

                #
                # If many processes competing to obtain lock, make sure to check for file existence again
                # once file lock is acquired.
                # It is possible some other competing processes have obtained it.
                # And thus we do a verification check below
                # Read back, as there might be another worker/thread that obtained the lock and wrote
                # something to it also.
                #
                t.sleep(0.01+random.uniform(-0.005,+0.005))
                # Should be 3 now
                LockFile.LOCKS_DICT[lock_file_path] += 1
                f = open(file=lock_file_path, mode='r')
                read_back_string = f.read()
                f.close()
                if (read_back_string == random_string) and (LockFile.LOCKS_DICT[lock_file_path] == 3):
                    lg.Log.debugdebug('Read back random string "' + str(read_back_string) + '" ok. Memory counter ok.')
                    return True
                else:
                    LockFile.N_RACE_CONDITIONS_FILE += 1
                    lg.Log.warning(
                        str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': File Race condition ' + str(LockFile.N_RACE_CONDITIONS_FILE)
                        + '! Round ' + str(round_count)
                        + '. Failed verify lock file with random string "'
                        + str(random_string) + '", got instead "' + str(read_back_string) + '".'
                    )
                    continue
            except Exception as ex_file:
                lg.Log.error(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Round ' + str(round_count) + '. Error lock file "' + str(lock_file_path)
                    + '": ' + str(ex_file)
                )
                continue
            finally:
                del LockFile.LOCKS_DICT[lock_file_path]

        return False

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

class LoadTestLockFile:
    X_SHARED = 0
    N_FAILED_LOCK = 0

    @staticmethod
    def incre_x(count, lock_file_path, max_wait_time_secs):
        for i in range(count):
            if LockFile.acquire_file_cache_lock(lock_file_path=lock_file_path, max_wait_time_secs=max_wait_time_secs):
                LoadTestLockFile.X_SHARED += 1
                print(str(LoadTestLockFile.X_SHARED) + ' Thread ' + str(threading.get_ident()))
                LockFile.release_file_cache_lock(lock_file_path=lock_file_path)
            else:
                LoadTestLockFile.N_FAILED_LOCK += 1
                print(
                    '***** ' + str(LoadTestLockFile.N_FAILED_LOCK)
                    + '. Failed to obtain lock: ' + str(LoadTestLockFile.X_SHARED)
                )
        print('***** THREAD ' + str(threading.get_ident()) + ' DONE ' + str(count) + ' COUNTS')

    def __init__(self, lock_file_path, max_wait_time_secs):
        self.lock_file_path = lock_file_path
        self.max_wait_time_secs = max_wait_time_secs
        return

    class CountThread(threading.Thread):
        def __init__(self, count, lock_file_path, max_wait_time_secs):
            super(LoadTestLockFile.CountThread, self).__init__()
            self.count = count
            self.lock_file_path = lock_file_path
            self.max_wait_time_secs = max_wait_time_secs

        def run(self):
            LoadTestLockFile.incre_x(
                count = self.count,
                lock_file_path = self.lock_file_path,
                max_wait_time_secs = self.max_wait_time_secs
            )

    def run(self):
        threads_list = []
        n = 10
        n_sum = 0
        n_threads = 100
        for i in range(n_threads):
            count = 50
            n_sum += count
            threads_list.append(LoadTestLockFile.CountThread(
                count=count,
                lock_file_path = self.lock_file_path,
                max_wait_time_secs = self.max_wait_time_secs
            ))
            print(str(i) + '. New thread "' + str(threads_list[i].getName()) + '" count ' + str(count))
        for i in range(len(threads_list)):
            thr = threads_list[i]
            print('Starting thread ' + str(i))
            thr.start()

        for thr in threads_list:
            thr.join()

        print('********* TOTAL SHOULD GET ' + str(n_sum) + '. Failed Counts = ' + str(LoadTestLockFile.N_FAILED_LOCK))
        print('********* TOTAL COUNT SHOULD BE = ' + str(n_sum - LoadTestLockFile.N_FAILED_LOCK))
        print('********* TOTAL RACE CONDITIONS MEMORY = ' + str(LockFile.N_RACE_CONDITIONS_MEMORY))
        print('********* TOTAL RACE CONDITIONS FILE = ' + str(LockFile.N_RACE_CONDITIONS_FILE))
        print('********* FAILED LOCKS SHOULD BE 0')


if __name__ == '__main__':
    lock_file_path = '/tmp/lockfile.test.lock'
    LockFile.release_file_cache_lock(lock_file_path=lock_file_path)

    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_WARNING
    LoadTestLockFile(
        lock_file_path = lock_file_path,
        max_wait_time_secs = 10
    ).run()

    exit(0)

    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_DEBUG_2
    res = LockFile.acquire_file_cache_lock(
        lock_file_path = lock_file_path,
        max_wait_time_secs = 1.2
    )
    print('Lock obtained = ' + str(res))
    res = LockFile.release_file_cache_lock(
        lock_file_path = lock_file_path
    )
    print('Lock released = ' + str(res))

    res = LockFile.acquire_file_cache_lock(
        lock_file_path = lock_file_path,
        max_wait_time_secs = 2.2
    )
    print('Lock obtained = ' + str(res))
