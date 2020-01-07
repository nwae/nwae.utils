
import os
import time as t
import datetime as dt
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo
import threading
import random
import uuid
from nwae.utils.Profiling import Profiling


#
# THEORY OF CLASH
#   Both Models below have been tested and is theoretically correct.
#
#   Model:
#     Let the frequency of checks for file lock availability be C per second
#     for each worker. As example let C=4.
#     Let the available lock "slots" available in 1s be S.
#     Since it takes about 0.3521 ms at 1% quantile, we assume the clash interval
#     at 0.35ms or about 3000-th of a second. If we assume the lock is held for
#     another period of time to do other things, we assume the lock is held for
#     10ms, or S=100.
#     Thus in 1s if S=100, there are only S=100 lock slots on offer.
#     If the number of threads competing is N>100, then some threads will not
#     gain a slot in that 1s window.
#     This means the probability of checking in any of the write slot is C/W
#     or about 1/100 (note it is not a Poisson).
#     This means in 1s, the probability of a thread not gaining a lock if in
#     total N threads are competing is given by the access slots max(0,N-S)
#     divided by total threads N
#            F(1) = P(Fail to obtain lock in 1s) = max(0,N-S)/N
#     Thus the probability of not obtaining lock in x seconds (assuming all N
#     threads are working forever, never stops) is
#            F(x) = F(1)/x
#
#   Empirical Model:
#     But for simplicity, we can use the following:
#     When N workers/processes/threads simultaneously access a resource, with
#     max wait time W, there is a probability of a worker never getting to access
#     this resource within this time W.
#     If the wait time W is doubled, the probability falls by half (not mathematically
#     correct actually).
#     If the number of threads N are doubled, the probability increases twice (also
#     not mathematically correct).
#     Thus
#          P(fail_to_obtain_lock) = k * N / W
#     The constant k depends on the machine, on a Mac Book Air, k = 1/250 = 0.005
#
class LockFile:

    N_RACE_CONDITIONS_MEMORY = 0
    N_RACE_CONDITIONS_FILE = 0

    # Not much point using memory locks as we are trying to lock cross process
    USE_LOCKS_MUTEX = False
    __LOCKS_MUTEX = {}

    #
    # If a lock file is older than 30 secs, remove forcefully.
    # No process should hold it for so long anyway.
    #
    FORCE_REMOVE_LOCKFILE_AGE_SECS_THRESHOLD = 30

    # For Mac Book Air
    K_CONSTANT_MAC_BOOK_AIR = 1 / 250
    # Slots available per second
    SLOTS_PER_SEC = 45

    def __init__(self):
        return

    @staticmethod
    def __wait_for_lock_file(
            lock_file_path,
            max_wait_time_secs
    ):
        total_sleep_time = 0.0

        while os.path.isfile(lock_file_path):
            #
            # Check lock file time, if older than certain threshold, remove it forcefully.
            # It is unlikely a process has had it for so long, or that process may have died
            # already.
            #
            # Check if file time is newer
            try:
                ftime = dt.datetime.fromtimestamp( os.path.getmtime(lock_file_path) )
                lockfile_age_secs = Profiling.get_time_dif_secs(start=ftime, stop=dt.datetime.now(), decimals=4)
            except Exception as ex_check_time:
                lockfile_age_secs = -1
                lg.Log.warning(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Exception checking time for lock file "' + str(lock_file_path)
                    + '", possible already released by another process. Exception: ' + str(ex_check_time)
                )

            if lockfile_age_secs > LockFile.FORCE_REMOVE_LOCKFILE_AGE_SECS_THRESHOLD:
                lg.Log.critical(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Trying to forcefully remove lock file "' + str(lock_file_path)
                    + '". Already ' + str(lockfile_age_secs) + ' seconds old.'
                )
                if LockFile.release_file_cache_lock(lock_file_path=lock_file_path):
                    lg.Log.warning(
                        str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Success. Forcefully removed lock file "' + str(lock_file_path)
                        + '". Already ' + str(lockfile_age_secs) + ' seconds old.'
                    )
                else:
                    lg.Log.critical(
                        str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Error. Failed to forcefully remove lock file "' + str(lock_file_path)
                        + '". Already ' + str(lockfile_age_secs) + ' seconds old.'
                    )

            lg.Log.important(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Waiting for file lock "' + str(lock_file_path)
                + '", ' + str(round(total_sleep_time,2))
                + 's. Lock file age = ' + str(lockfile_age_secs) + 's.'
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
            # At 10s max wait time, this means the probability of not obtaining lock if
            # 10 processes simultaneously wants to access it is roughly (1/250)*10/10 = 0.4%
            max_wait_time_secs = 10.0,
            verbose = 0
    ):
        if lock_file_path is None:
            lg.Log.warning(
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
            if total_wait_time >= max_wait_time_secs:
                lg.Log.critical(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Round ' + str(round_count)
                    + '. Failed to get lock ~' + str(total_wait_time) + 's to file "'
                    + str(lock_file_path) + '"! Very likely process is being bombarded with too many requests.'
                )
                return False
            round_count += 1

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

            try:
                #
                # We use additional memory lock for race conditions
                # But mutex/memory locks only good enough for threads in the same process, not
                # for cross workers.
                if LockFile.USE_LOCKS_MUTEX:
                    if lock_file_path not in LockFile.__LOCKS_MUTEX:
                        LockFile.__LOCKS_MUTEX[lock_file_path] = threading.Lock()
                    LockFile.__LOCKS_MUTEX[lock_file_path].acquire()

                f = open(file=lock_file_path, mode='w')
                timestamp = dt.datetime.now()
                random_string = uuid.uuid4().hex + ' ' + str(timestamp) + ' ' + str(threading.get_ident())
                lg.Log.debug(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Write random string "' + str(random_string) + '" to lock file "' + str(lock_file_path) + '".'
                )
                f.write(random_string)
                f.close()

                #
                # If many processes competing to obtain lock, means many processes will arrive here simultaneously.
                # Read back, as there might be another worker/thread that reached this point and wrote
                # something to it also. This can handle cross process clashes, unlike memory locks.
                #
                # The time stats for writing a lock file (test function below) is the following in milliseconds:
                #   {'average': 0.6627,
                #   'quantile': {'0.001%': 0.3521, '1.0%': 0.369, '10.0%': 0.407,
                #   '25.0%': 0.447, '50.0%': 0.523, '75.0%': 0.67, '90.0%': 0.898, '99.0%': 1.966,
                #   '99.999%': 176.8324}}
                # This means by sleeping between 10ms to 15ms is more than enough to cover at least 99% (1.966ms)
                # of the cases.
                # Meaning to say if there are race conditions, after the sleep, all competitors would have
                # already written to the file, thus when reading back, only 1 competitor will see it correctly.
                t.sleep(0.01+random.uniform(0.0, 0.005))
                lg.Log.debug(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Check random string "' + str(random_string) + '" from lock file "' + str(lock_file_path) + '".'
                )
                f = open(file=lock_file_path, mode='r')
                read_back_string = f.read()
                f.close()
                if (read_back_string == random_string):
                    lg.Log.debugdebug('Read back random string "' + str(read_back_string) + '" ok.')
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
                if LockFile.USE_LOCKS_MUTEX:
                    LockFile.__LOCKS_MUTEX[lock_file_path].release()

        return False

    @staticmethod
    def release_file_cache_lock(
            lock_file_path,
            verbose = 0
    ):
        if lock_file_path is None:
            lg.Log.warning(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Lock file is None type, why release lock?!'
            )
            return False

        if not os.path.isfile(lock_file_path):
            lg.Log.warning(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': No lock file "' + str(lock_file_path) + '" to release!!'
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

    @staticmethod
    def get_time_stats_to_create_lock_file(
            lock_file_path,
            n_rounds = 1000
    ):
        x = []

        for i in range(n_rounds):
            a = Profiling.start()
            f = open(file=lock_file_path, mode='w')
            timestamp = dt.datetime.now()
            random_string = uuid.uuid4().hex + ' ' + str(timestamp) + ' ' + str(threading.get_ident())
            lg.Log.debug(
                str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Write random string "' + str(random_string) + '" to lock file "' + str(lock_file_path) + '".'
            )
            f.write(random_string)
            f.close()
            time_taken_millisecs = Profiling.get_time_dif_secs(start=a, stop=Profiling.stop(), decimals=6) * 1000
            x.append(time_taken_millisecs)
            print(str(i+1) + ': ' + str(time_taken_millisecs) + 'ms')

        import numpy as np
        x_np = np.array(x)
        quantiles = {}
        for q in [0.001, 1.0, 10.0, 25.0, 50.0, 75.0, 90.0, 99.0, 99.999]:
            quantiles[str(q)+'%'] = round(np.quantile(x_np, q/100), 4)

        return {
            'average': round(x_np.mean(),4),
            'quantile': quantiles
        }


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

    def __init__(self, lock_file_path, max_wait_time_secs, n_threads, count_to):
        self.lock_file_path = lock_file_path
        self.max_wait_time_secs = max_wait_time_secs
        self.n_threads = n_threads
        self.count_to = count_to
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
        n_sum = 0
        for i in range(self.n_threads):
            n_sum += self.count_to
            threads_list.append(LoadTestLockFile.CountThread(
                count = self.count_to,
                lock_file_path = self.lock_file_path,
                max_wait_time_secs = self.max_wait_time_secs
            ))
            print(str(i) + '. New thread "' + str(threads_list[i].getName()) + '" count ' + str(self.count_to))
        for i in range(len(threads_list)):
            thr = threads_list[i]
            print('Starting thread ' + str(i))
            thr.start()

        for thr in threads_list:
            thr.join()

        print('********* THREADS N=' + str(self.n_threads) + ', WAIT=' + str(self.max_wait_time_secs) + 's.')
        print('********* TOTAL SHOULD GET ' + str(n_sum) + '. Failed Counts = ' + str(LoadTestLockFile.N_FAILED_LOCK))
        print('********* TOTAL COUNT SHOULD BE = ' + str(n_sum - LoadTestLockFile.N_FAILED_LOCK))
        print('********* TOTAL RACE CONDITIONS MEMORY = ' + str(LockFile.N_RACE_CONDITIONS_MEMORY))
        print('********* TOTAL RACE CONDITIONS FILE = ' + str(LockFile.N_RACE_CONDITIONS_FILE))
        print('********* PROBABILITY OF FAILED LOCKS = ' + str(round(LoadTestLockFile.N_FAILED_LOCK / n_sum, 4)))
        N = self.n_threads
        x = self.max_wait_time_secs
        F_1 = max(0, N-LockFile.SLOTS_PER_SEC) / N
        print('********* THEO PROBABILITY OF FAILED LOCKS (Theo Model) = '
              + str(round(F_1/x, 4)))
        print('********* THEO PROBABILITY OF FAILED LOCKS (Empirical Model) = '
              + str(round(LockFile.K_CONSTANT_MAC_BOOK_AIR * self.n_threads / self.max_wait_time_secs, 4)))


if __name__ == '__main__':
    lock_file_path = '/tmp/lockfile.test.lock'

    test = 'load test lock file'

    if test == 'lock file stats':
        print('Average time to create lock file = ')
        print(LockFile.get_time_stats_to_create_lock_file(lock_file_path=lock_file_path, n_rounds=10000))
        exit(0)

    if test == 'load test lock file':
        lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_INFO
        LoadTestLockFile(
            lock_file_path = lock_file_path,
            # From trial and error, for 100 simultaneous threads, each counting to 50,
            # waiting for max 10 secs, the probability of failed lock is about 100/5000
            # If the wait time W is doubled, the probability falls by half.
            # If the number of threads N are doubled, the probability increases twice.
            # Thus P(fail_lock) = k * N / W
            # The constant k depends on the machine, on a Mac Book Air, k = 1/200 = 0.005
            max_wait_time_secs = 8.8,
            n_threads = 120,
            # The probability of failed lock does not depend on this, this is just sampling
            count_to = 20
        ).run()

    if test == '':
        lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_DEBUG_2
        res = LockFile.acquire_file_cache_lock(
            lock_file_path = lock_file_path,
            max_wait_time_secs = 30
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
