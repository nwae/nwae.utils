
import pickle
import os
import nwae.utils.LockFile as lockfile
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo
import threading
import random
import time
import nwae.utils.UnitTest as nwaeut


#
# Serializes Python object to file, for multi-worker, multi-thread persistence
#
class ObjectPersistence:

    ATOMIC_UPDATE_MODE_ADD = 'add'
    ATOMIC_UPDATE_MODE_REMOVE = 'remove'

    DEFAULT_WAIT_TIME_LOCK_FILE = 30

    def __init__(
            self,
            default_obj,
            obj_file_path,
            lock_file_path
    ):
        self.default_obj = default_obj
        self.obj_file_path = obj_file_path
        self.lock_file_path = lock_file_path

        # Read once from storage
        self.obj = None
        self.obj = self.read_persistent_object()
        lg.Log.debug(
            str(__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': New object persistence created from "' + str(self.obj_file_path)
            + '", lock file "' + str(self.lock_file_path) + '" as: ' + str(self.obj)
        )
        return

    def __assign_default_object_copy(self):
        try:
            self.obj = self.default_obj.copy()
        except Exception as ex_copy:
            errmsg = str(__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ': Failed to assign copy of default object: ' + str(ex_copy) \
                     + '. This will potentially modify default object!'
            lg.Log.error(errmsg)
            self.obj = self.default_obj

    #
    # Makes sure that read/write happens in one go
    #
    def atomic_update(
            self,
            # Only dict type supported, will add a new items to dict
            new_items,
            # 'add' or 'remove'
            mode,
            max_wait_time_secs = DEFAULT_WAIT_TIME_LOCK_FILE
    ):
        if not lockfile.LockFile.acquire_file_cache_lock(
                lock_file_path = self.lock_file_path,
                max_wait_time_secs = max_wait_time_secs
        ):
            lg.Log.critical(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Atomic update could not serialize to "' + str(self.obj_file_path)
                + '", could not obtain lock to "' + str(self.lock_file_path) + '".'
            )
            return False

        try:
            self.obj = ObjectPersistence.deserialize_object_from_file(
                obj_file_path  = self.obj_file_path,
                # We already obtained lock manually
                lock_file_path = None
            )
            if self.obj is None:
                lg.Log.warning(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Atomic update cannot deserialize from file.'
                )
                self.__assign_default_object_copy()

            lg.Log.debug(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Cache object type ' + str(type(self.obj))
            )

            if type(self.obj) is dict:
                if type(new_items) is not dict:
                    lg.Log.error(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Atomic updates to dict type must be a dict item! Got item type "'
                        + str(type(new_items)) + '": ' + str(new_items)
                    )
                    return False
                for k in new_items.keys():
                    if mode == ObjectPersistence.ATOMIC_UPDATE_MODE_ADD:
                        self.obj[k] = new_items[k]
                        lg.Log.info(
                            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Atomic update added new item ' + str(new_items)
                        )
                    elif mode == ObjectPersistence.ATOMIC_UPDATE_MODE_REMOVE:
                        if k in self.obj.keys():
                            del self.obj[k]
                            lg.Log.info(
                                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                + ': Atomic update removed item ' + str(new_items)
                            )
                    else:
                        lg.Log.error(
                            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Atomic update invalid mode "'+ str(mode) + '"!'
                        )
                        return False
            elif type(self.obj) is list:
                # In this mode, new items is only ONE item, otherwise you get unexpected results
                if mode == ObjectPersistence.ATOMIC_UPDATE_MODE_ADD:
                    self.obj.append(new_items)
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Atomic update added new items ' + str(new_items)
                    )
                elif mode == ObjectPersistence.ATOMIC_UPDATE_MODE_REMOVE:
                    if new_items in self.obj:
                        self.obj.remove(new_items)
                        lg.Log.error(
                            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Atomic updates removed item "' + str(new_items)
                            + str(type(self.obj)) + '"!'
                        )
            else:
                lg.Log.error(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Atomic updates not supported for cache type "'
                    + str(type(self.obj)) + '"!'
                )
                return False

            res = ObjectPersistence.serialize_object_to_file(
                obj = self.obj,
                obj_file_path = self.obj_file_path,
                lock_file_path = None
            )
            if not res:
                lg.Log.error(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Atomic update new item ' + str(new_items)
                    + ' fail, could not serialize update to file "' + str(self.obj_file_path) + '"'
                )
                return False
        except Exception as ex:
            lg.Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Atomic update new item ' + str(new_items)
                + ' fail. Exception update to file "' + str(self.obj_file_path) + '": ' + str(ex)
            )
            return False
        finally:
            lockfile.LockFile.release_file_cache_lock(
                lock_file_path = self.lock_file_path
            )
        return True

    #
    # Wrapper write function to applications
    #
    def update_persistent_object(
            self,
            new_obj,
            max_wait_time_secs = DEFAULT_WAIT_TIME_LOCK_FILE
    ):
        self.obj = new_obj
        res = ObjectPersistence.serialize_object_to_file(
            obj            = self.obj,
            obj_file_path  = self.obj_file_path,
            lock_file_path = self.lock_file_path,
            max_wait_time_secs = max_wait_time_secs
        )
        if not res:
            lg.Log.error(
                str(__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error writing to file "' + str(self.obj_file_path)
                + '", lock file "' + str(self.lock_file_path) + '" for data: ' + str(self.obj)
            )
        return res

    #
    # Wrapper read function for applications
    #
    def read_persistent_object(
            self,
            max_wait_time_secs = DEFAULT_WAIT_TIME_LOCK_FILE
    ):
        obj_read = ObjectPersistence.deserialize_object_from_file(
            obj_file_path  = self.obj_file_path,
            lock_file_path = self.lock_file_path,
            max_wait_time_secs = max_wait_time_secs
        )
        if obj_read is not None:
            self.obj = obj_read
        else:
            lg.Log.warning(
                str(__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': None object from file "' + str(self.obj_file_path)
                + '", lock file "' + str(self.lock_file_path) + '". Returning memory object.'
            )

        if type(self.default_obj) != type(self.obj):
            lg.Log.warning(
                str(__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Object read from file "' + str(self.obj_file_path)
                + '" of type "' + str(type(self.obj)) + ', different with default obj type "'
                + str(type(self.default_obj)) + '". Setting obj back to default obj.'
            )
            self.__assign_default_object_copy()
            # Need to write back to correct the object type
            self.update_persistent_object(
                new_obj = self.obj
            )

        return self.obj

    @staticmethod
    def serialize_object_to_file(
            obj,
            obj_file_path,
            # If None, means we don't obtain lock. Caller might already have the lock.
            lock_file_path = None,
            max_wait_time_secs = DEFAULT_WAIT_TIME_LOCK_FILE,
            verbose = 0
    ):
        if lock_file_path is not None:
            if not lockfile.LockFile.acquire_file_cache_lock(
                    lock_file_path = lock_file_path,
                    max_wait_time_secs = max_wait_time_secs
            ):
                lg.Log.critical(
                    str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Could not serialize to "' + str(obj_file_path) + '", could not obtain lock to "'
                    + str(lock_file_path) + '".'
                )
                return False

        try:
            if obj_file_path is None:
                lg.Log.critical(
                    str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Object file path "' + str(obj_file_path) + '" is None type!'
                )
                return False

            fhandle = open(
                file = obj_file_path,
                mode = 'wb'
            )
            pickle.dump(
                obj      = obj,
                file     = fhandle,
                protocol = pickle.HIGHEST_PROTOCOL
            )
            fhandle.close()
            lg.Log.debug(
                str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Object "' + str(obj)
                + '" serialized successfully to file "' + str(obj_file_path) + '"'
            )
            return True
        except Exception as ex:
            lg.Log.critical(
                str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Exception deserializing/loading object from file "'
                + str(obj_file_path) + '". Exception message: ' + str(ex) + '.'
            )
            return False
        finally:
            if lock_file_path is not None:
                lockfile.LockFile.release_file_cache_lock(
                    lock_file_path = lock_file_path,
                    verbose        = verbose
                )

    @staticmethod
    def deserialize_object_from_file(
            obj_file_path,
            # If None, means we don't obtain lock. Caller might already have the lock.
            lock_file_path = None,
            max_wait_time_secs = DEFAULT_WAIT_TIME_LOCK_FILE,
            verbose=0
    ):
        if not os.path.isfile(obj_file_path):
            lg.Log.warning(
                str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': No object file "' + str(obj_file_path) + '" found.'
            )
            return None

        if lock_file_path is not None:
            if not lockfile.LockFile.acquire_file_cache_lock(
                lock_file_path = lock_file_path,
                max_wait_time_secs = max_wait_time_secs
            ):
                lg.Log.critical(
                    str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Could not deserialize from "' + str(obj_file_path) + '", could not obtain lock to "'
                    + str(lock_file_path) + '".'
                )
                return None

        try:
            fhandle = open(
                file = obj_file_path,
                mode = 'rb'
            )
            obj = pickle.load(
                file = fhandle
            )
            fhandle.close()
            lg.Log.debug(
                str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Object "' + str(obj) + '" deserialized successfully from file "' + str(obj_file_path)
                + '" to ' + str(obj) + '.')

            return obj
        except Exception as ex:
            lg.Log.critical(
                str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Exception deserializing/loading object from file "'
                + str(obj_file_path) + '". Exception message: ' + str(ex) + '.'
            )
            return None
        finally:
            if lock_file_path is not None:
                lockfile.LockFile.release_file_cache_lock(
                    lock_file_path = lock_file_path
                )


#
# We do extreme testing on ObjectPersistence, by running hundreds of threads updating
# a single file.
# We then check back if there are any errors.
#
class LoadTest:

    DELETED_KEYS_SET = set()

    def __init__(self, obj_file_path, lock_file_path, max_wait_time_secs, n_threads, count_to):
        self.obj_file_path = obj_file_path
        self.lock_file_path = lock_file_path
        self.max_wait_time_secs = max_wait_time_secs
        self.n_threads = n_threads
        self.count_to = count_to
        return

    class CountThread(threading.Thread):
        def __init__(self, thread_num, cache, count_to, max_wait_time_secs):
            super(LoadTest.CountThread, self).__init__()
            self.thread_num = thread_num
            self.cache = cache
            self.count_to = count_to
            self.max_wait_time_secs = max_wait_time_secs

        def run(self):
            for i in range(self.count_to):
                # To ensure all values are unique, "count_to" is the mathematical base
                value = self.count_to*self.thread_num + i
                self.cache.atomic_update(
                    new_items = {value: threading.get_ident()},
                    mode = ObjectPersistence.ATOMIC_UPDATE_MODE_ADD
                )
                lg.Log.info('Value=' + str(value) + ' +++ ' + str(self.cache.read_persistent_object()))
                # Delete something at random
                if random.choice([0,1]) == 1:
                    obj = self.cache.read_persistent_object()
                    key_choices = list(obj.keys())
                    if len(key_choices) > 0:
                        random_key_to_delete = random.choice(key_choices)
                        self.cache.atomic_update(
                            new_items = {random_key_to_delete: obj[random_key_to_delete]},
                            mode = ObjectPersistence.ATOMIC_UPDATE_MODE_REMOVE
                        )
                        LoadTest.DELETED_KEYS_SET.add(random_key_to_delete)
                        lg.Log.info('DELETED ' + str(random_key_to_delete))
                time.sleep(random.uniform(0.005,0.010))
            lg.Log.info('***** THREAD ' + str(threading.get_ident()) + ' DONE ' + str(self.count_to) + ' COUNTS')

    def run_unit_test(self):
        threads_list = []
        n_sum = 0
        for i in range(self.n_threads):
            n_sum += self.count_to
            threads_list.append(LoadTest.CountThread(
                thread_num = i,
                cache = ObjectPersistence(
                    default_obj = {},
                    obj_file_path = self.obj_file_path,
                    lock_file_path = self.lock_file_path
                ),
                count_to = self.count_to,
                max_wait_time_secs = self.max_wait_time_secs
            ))
            lg.Log.important(str(i) + '. New thread "' + str(threads_list[i].getName()) + '" count ' + str(self.count_to))
        expected_values = []
        for i in range(len(threads_list)):
            for j in range(self.count_to):
                expected_values.append(self.count_to*i + j)
            thr = threads_list[i]
            lg.Log.important('Starting thread ' + str(i))
            thr.start()

        for thr in threads_list:
            thr.join()

        cache = ObjectPersistence(
            default_obj={},
            obj_file_path=self.obj_file_path,
            lock_file_path=self.lock_file_path
        )
        lg.Log.important('********* Final Object File: ' + str(cache.read_persistent_object()))
        values = list(cache.read_persistent_object().keys())
        lg.Log.important('Added Keys: ' + str(values))
        lg.Log.important('Deleted Keys: ' + str(LoadTest.DELETED_KEYS_SET))
        lg.Log.important('Total Added = ' + str(len(values)))
        lg.Log.important('Total Deleted = ' + str(len(LoadTest.DELETED_KEYS_SET)))
        values.sort()
        expected_values = list( set(expected_values) - LoadTest.DELETED_KEYS_SET )
        expected_values.sort()
        test_pass = values == expected_values
        lg.Log.important('PASS = ' + str(test_pass))
        lg.Log.important('Values:   ' + str(values))
        lg.Log.important('Expected: ' + str(expected_values))
        return nwaeut.ResultObj(count_ok=1*test_pass, count_fail=1*(not test_pass))


class UnitTestObjectPersistence:

    def __init__(self, ut_params):
        self.ut_params = ut_params
        if self.ut_params is None:
            self.ut_params = nwaeut.UnitTestParams
        return

    def __remove_files(self, obj_file_path, lock_file_path):
        try:
            os.remove(obj_file_path)
        except Exception:
            pass
        try:
            os.remove(lock_file_path)
        except Exception:
            pass

    def run_unit_test(self):
        obj_file_path = '/tmp/loadtest.objpers.obj'
        lock_file_path = '/tmp/loadtest.objpers.obj.lock'

        #
        # If we don't do this the test will fail as the upcoming threads,
        # many of them will try to delete the file due to timeout, and will
        # accidentally delete one created by another thread
        #
        self.__remove_files(obj_file_path=obj_file_path, lock_file_path=lock_file_path)

        res_load_test = LoadTest(
            obj_file_path  = obj_file_path,
            lock_file_path = lock_file_path,
            count_to       = 5,
            n_threads      = 30,
            max_wait_time_secs = 30
        ).run_unit_test()

        res_other = nwaeut.ResultObj(count_ok=0, count_fail=0)
        obj_file_path = '/tmp/objPersTest.b'
        lock_file_path = '/tmp/lock.objPersTest.b'
        self.__remove_files(obj_file_path=obj_file_path, lock_file_path=lock_file_path)

        objects = [
            {
                'a': [1, 2, 3],
                'b': 'test object'
            },
            # Empty objects
            [],
            {},
            88,
            'eighty eight'
        ]

        for obj in objects:
            ObjectPersistence.serialize_object_to_file(
                obj            = obj,
                obj_file_path  = obj_file_path,
                lock_file_path = lock_file_path
            )

            b = ObjectPersistence.deserialize_object_from_file(
                obj_file_path  = obj_file_path,
                lock_file_path = lock_file_path
            )
            lg.Log.info(str(b))
            ok = obj == b
            res_other.count_ok += 1 * ok
            res_other.count_fail += 1 * (not ok)

        obj_file_path = '/tmp/objPersTestAtomicUpdate.d'
        lock_file_path = '/tmp/lock.objPersTestAtomicUpdate.d'
        self.__remove_files(obj_file_path=obj_file_path, lock_file_path=lock_file_path)
        x = ObjectPersistence(
            default_obj    = {},
            obj_file_path  = obj_file_path,
            lock_file_path = lock_file_path
        )
        lg.Log.info(x.atomic_update(new_items={1: 'hana', 2: 'dul'}, mode=ObjectPersistence.ATOMIC_UPDATE_MODE_ADD))
        ok = x.read_persistent_object() == {1: 'hana', 2: 'dul'}
        res_other.count_ok += 1 * ok
        res_other.count_fail += 1 * (not ok)
        lg.Log.info(x.atomic_update(new_items={1: 'hana'}, mode=ObjectPersistence.ATOMIC_UPDATE_MODE_REMOVE))
        ok = x.read_persistent_object() == {2: 'dul'}
        res_other.count_ok += 1 * ok
        res_other.count_fail += 1 * (not ok)
        lg.Log.info(x.atomic_update(new_items={3: 'set'}, mode=ObjectPersistence.ATOMIC_UPDATE_MODE_ADD))
        ok = x.read_persistent_object() == {2: 'dul', 3: 'set'}
        res_other.count_ok += 1 * ok
        res_other.count_fail += 1 * (not ok)

        # Purposely write wrong type
        x.update_persistent_object(new_obj=[1,2,3])
        x = ObjectPersistence(
            default_obj    = {},
            obj_file_path  = obj_file_path,
            lock_file_path = lock_file_path
        )
        ok = x.read_persistent_object() == {}
        res_other.count_ok += 1 * ok
        res_other.count_fail += 1 * (not ok)

        res_final = nwaeut.ResultObj(
            count_ok = res_load_test.count_ok + res_other.count_ok,
            count_fail = res_load_test.count_fail + res_other.count_fail
        )
        lg.Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Object Persistence Unit Test PASS ' + str(res_final.count_ok) + ' FAIL ' + str(res_final.count_fail)
        )
        return res_final


if __name__ == '__main__':
    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_INFO

    res = UnitTestObjectPersistence(ut_params=None).run_unit_test()
    exit(res.count_fail)
