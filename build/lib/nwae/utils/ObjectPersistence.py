
import pickle
import os
import nwae.utils.LockFile as lockfile
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


#
# Serializes Python object to file, for multi-worker, multi-thread persistence
#
class ObjectPersistence:

    def __init__(self):
        return

    @staticmethod
    def serialize_object_to_file(
            obj,
            obj_file_path,
            lock_file_path = None,
            verbose = 0
    ):
        if lock_file_path is not None:
            lockfile.LockFile.acquire_file_cache_lock(
                lock_file_path = lock_file_path,
                verbose        = verbose
            )

        try:
            if obj_file_path is None:
                lg.Log.critical(str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                + ' ' + str(getframeinfo(currentframe()).lineno)
                           + ': Object file path "' + str(obj_file_path) + '" is None type!')
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
            lg.Log.debug(str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                         + ' ' + str(getframeinfo(currentframe()).lineno)
                         + ': Object "' + str(obj)
                         + '" serialized successfully to file "' + str(obj_file_path) + '"')
            return True
        except Exception as ex:
            lg.Log.critical(str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Exception deserializing/loading object from file "'
                            + str(obj_file_path) + '". Exception message: ' + str(ex) + '.')
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
            lock_file_path=None,
            verbose=0
    ):
        if not os.path.isfile(obj_file_path):
            lg.Log.critical(str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ' No object file "' + str(obj_file_path) + '" found!!')
            return None

        if lock_file_path is not None:
            lockfile.LockFile.acquire_file_cache_lock(
                lock_file_path=lock_file_path,
                verbose=verbose
            )

        try:
            fhandle = open(
                file = obj_file_path,
                mode = 'rb'
            )
            obj = pickle.load(
                file = fhandle
            )
            lg.Log.debug(str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                         + ' ' + str(getframeinfo(currentframe()).lineno)
                         + ': Object "' + str(obj)
                         + '" deserialized successfully from file "' + str(obj_file_path) + '" to '
                         + str(obj) + '.')

            return obj
        except Exception as ex:
            lg.Log.critical(str(ObjectPersistence.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Exception deserializing/loading object from file "'
                            + str(obj_file_path) + '". Exception message: ' + str(ex) + '.')
            return None
        finally:
            if lock_file_path is not None:
                lockfile.LockFile.release_file_cache_lock(
                    lock_file_path = lock_file_path,
                    verbose        = verbose
                )


if __name__ == '__main__':
    obj_file_path = '/tmp/pickleObj.b'
    lock_file_path = '/tmp/.lock.pickleObj.b'

    obj = {
        'a': [1,2,3],
        'b': 'test object'
    }

    ObjectPersistence.serialize_object_to_file(
        obj = obj,
        obj_file_path = obj_file_path,
        lock_file_path = lock_file_path,
        verbose = 3
    )

    b = ObjectPersistence.deserialize_object_from_file(
        obj_file_path = obj_file_path,
        lock_file_path = lock_file_path,
        verbose = 3
    )
    print(str(b))