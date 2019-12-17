
import os
import time as t
import datetime as dt
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo
import threading
import random
import uuid


#
# THEORY OF CLASH
#   Model:
#     Let the probability of clash be c for 2 random parties accessing a time
#     slot of t.
#     Thus if there are n parties, the clash probability P(n) of n clashes
#     is just a Bernoulli.
#
# But for simplicity, we can use the following:
# When N workers/processes/threads simultaneously access a resource, with
# max wait time W, there is a probability of a worker never getting to access
# this resource within this time W.
# If the wait time W is doubled, the probability falls by half (not mathematically
# correct actually).
# If the number of threads N are doubled, the probability increases twice (also
# not mathematically correct).
# Thus
#
#      P(fail_to_obtain_lock) = k * N / W
#
# The constant k depends on the machine, on a Mac Book Air, k = 1/250 = 0.005
#
class LockFile:

    N_RACE_CONDITIONS_MEMORY = 0
    N_RACE_CONDITIONS_FILE = 0

    # Not much point using memory locks as we are trying to lock cross process
    USE_LOCKS_MUTEX = False
    __LOCKS_MUTEX = {}

    # For Mac Book Air
    K_CONSTANT_MAC_BOOK_AIR = 1 / 250

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
            # At 10s max wait time, this means the probability of not obtaining lock if
            # 10 processes simultaneously wants to access it is roughly (1/250)*10/10 = 0.4%
            max_wait_time_secs = 10.0,
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
            if total_wait_time >= max_wait_time_secs:
                lg.Log.critical(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Round ' + str(round_count)
                    + '. Failed to get lock ~' + str(total_wait_time) + 's. Other competing process won lock to file "'
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
                # If many processes competing to obtain lock, make sure to check for file existence again
                # once file lock is acquired.
                # It is possible some other competing processes have obtained it.
                # And thus we do a verification check below
                # Read back, as there might be another worker/thread that obtained the lock and wrote
                # something to it also. This can handle cross process, unlike memory locks.
                #
                t.sleep(0.01+random.uniform(-0.005,+0.005))
                lg.Log.debug(
                    str(LockFile.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Check random string "' + str(random_string) + '" from lock file "' + str(lock_file_path) + '".'
                )
                f = open(file=lock_file_path, mode='r')
                read_back_string = f.read()
                f.close()
                if (read_back_string == random_string):
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
                if LockFile.USE_LOCKS_MUTEX:
                    LockFile.__LOCKS_MUTEX[lock_file_path].release()

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

        print('********* TOTAL SHOULD GET ' + str(n_sum) + '. Failed Counts = ' + str(LoadTestLockFile.N_FAILED_LOCK))
        print('********* TOTAL COUNT SHOULD BE = ' + str(n_sum - LoadTestLockFile.N_FAILED_LOCK))
        print('********* TOTAL RACE CONDITIONS MEMORY = ' + str(LockFile.N_RACE_CONDITIONS_MEMORY))
        print('********* TOTAL RACE CONDITIONS FILE = ' + str(LockFile.N_RACE_CONDITIONS_FILE))
        print('********* PROBABILITY OF FAILED LOCKS = ' + str(round(LoadTestLockFile.N_FAILED_LOCK / n_sum, 4)))
        print('********* THEO PROBABILITY OF FAILED LOCKS = '
              + str(round(LockFile.K_CONSTANT_MAC_BOOK_AIR * self.n_threads / self.max_wait_time_secs, 4)))


if __name__ == '__main__':
    lock_file_path = '/tmp/lockfile.test.lock'
    LockFile.release_file_cache_lock(lock_file_path=lock_file_path)

    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_INFO
    LoadTestLockFile(
        lock_file_path = lock_file_path,
        # From trial and error, for 100 simultaneous threads, each counting to 50,
        # waiting for max 10 secs, the probability of failed lock is about 100/5000
        # If the wait time W is doubled, the probability falls by half.
        # If the number of threads N are doubled, the probability increases twice.
        # Thus P(fail_lock) = k * N / W
        # The constant k depends on the machine, on a Mac Book Air, k = 1/200 = 0.005
        max_wait_time_secs = 10,
        n_threads = 100,
        # The probability of failed lock does not depend on this, this is just sampling
        count_to = 10
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
