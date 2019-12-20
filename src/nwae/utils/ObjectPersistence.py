
import pickle
import os
import nwae.utils.LockFile as lockfile
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


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
        lg.Log.info(
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
                lg.Log.error(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Atomic update fail, cannot deserialize from file.'
                )
                self.__assign_default_object_copy()

            print('cache object type ' + str(type(self.obj)))

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
            lg.Log.error(
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
            lg.Log.critical(
                str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': No object file "' + str(obj_file_path) + '" found!!'
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


if __name__ == '__main__':
    obj_file_path = '/tmp/pickleObj.b'
    lock_file_path = '/tmp/.lock.pickleObj.b'

    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_INFO

    objects = [
        {
            'a': [1,2,3],
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
            obj = obj,
            obj_file_path = obj_file_path,
            lock_file_path = lock_file_path
        )

        b = ObjectPersistence.deserialize_object_from_file(
            obj_file_path = obj_file_path,
            lock_file_path = lock_file_path
        )
        print(str(b))

    obj_file_path = '/tmp/pickleObj.d'
    lock_file_path = '/tmp/.lock.pickleObj.d'
    x = ObjectPersistence(
        default_obj = {},
        obj_file_path = obj_file_path,
        lock_file_path = lock_file_path
    )
    print(x.atomic_update(new_items={1:'hana', 2:'dul'}, mode = ObjectPersistence.ATOMIC_UPDATE_MODE_ADD))
    print(x.read_persistent_object())
    print(x.atomic_update(new_items={1:'hana'}, mode = ObjectPersistence.ATOMIC_UPDATE_MODE_REMOVE))
    print(x.read_persistent_object())
    print(x.atomic_update(new_items={3:'set'}, mode = ObjectPersistence.ATOMIC_UPDATE_MODE_ADD))
    print(x.read_persistent_object())
