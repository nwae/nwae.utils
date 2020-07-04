
import threading
import datetime as dt
import time as t
import nwae.utils.Profiling as prf
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


#
# Base class for data caches, for single table/view from any data source.
# Steps:
#   1. Inherit this class
#   2. If you don't already have one, create a data object class <<MyDataObject>>.
#   2. Implement methods get_row_by_id() and get_all_data() using <<MyDataObject>>.
#
# See main() example below.
#
class BaseDataCache(threading.Thread):

    THREAD_SLEEP_TIME = 5

    # 5 minutes default
    CACHE_EXPIRE_SECS = 5*60

    # Singletons by bot key or any identifier
    SINGLETON_OBJECT = {}
    SINGLETON_OBJECT_MUTEX = threading.Lock()

    @staticmethod
    def get_singleton(
            DerivedClass,
            cache_identifier,
            # Must possess the get() method
            db_obj,
            # To be passed in to the get method()
            db_table_id_name,
            cache_expiry_time_secs = CACHE_EXPIRE_SECS
    ):
        DerivedClass.SINGLETON_OBJECT_MUTEX.acquire()

        try:
            if cache_identifier in BaseDataCache.SINGLETON_OBJECT.keys():
                if DerivedClass.SINGLETON_OBJECT[cache_identifier] is not None:
                    lg.Log.important(
                        str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Returning existing singleton object for db cache for botkey "'
                        + str(cache_identifier) + '".'
                    )
                    return DerivedClass.SINGLETON_OBJECT[cache_identifier]
            # Create new instance
            singleton = DerivedClass(
                cache_identifier = cache_identifier,
                db_obj           = db_obj,
                db_table_id_name = db_table_id_name,
                expire_secs      = cache_expiry_time_secs
            )
            # Don't start until called to start
            # singleton.start()
            DerivedClass.SINGLETON_OBJECT[cache_identifier] = singleton
            lg.Log.important(
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Created new singleton object for db cache for cache identifier "'
                + str(cache_identifier) + '".'
            )
            return DerivedClass.SINGLETON_OBJECT[cache_identifier]
        except Exception as ex:
            errmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception occurred getting singleton object for cache identifier "'\
                     + str(cache_identifier) + '". Exception message: ' + str(ex) + '.'
            lg.Log.critical(errmsg)
            raise Exception(errmsg)
        finally:
            DerivedClass.SINGLETON_OBJECT_MUTEX.release()

    @staticmethod
    def stop_singleton_job(
            DerivedClass,
            cache_identifier
    ):
        DerivedClass.SINGLETON_OBJECT_MUTEX.acquire()
        try:
            lg.Log.critical(
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Stopping cache "' + str(cache_identifier) + '"..'
            )
            DerivedClass.SINGLETON_OBJECT[cache_identifier].join()
        except Exception as ex:
            errmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception stopping singleton object for cache identifier "' + str(cache_identifier)\
                     + '". Exception message: ' + str(ex) + '.'
            lg.Log.critical(errmsg)
        finally:
            DerivedClass.SINGLETON_OBJECT_MUTEX.release()

    def __init__(
            self,
            cache_identifier,
            db_obj,
            db_table_id_name,
            expire_secs = CACHE_EXPIRE_SECS,
            # If None, means we reload all only once and quit thread
            reload_all_every_n_secs = None
    ):
        super(BaseDataCache, self).__init__()

        self.cache_identifier = cache_identifier
        self.db_obj = db_obj
        self.db_table_id_name = db_table_id_name

        self.expire_secs = expire_secs
        self.reload_all_every_n_secs = reload_all_every_n_secs

        # Keep in a dict
        self.__db_cache = {}
        self.__db_cache_last_update_time = {}
        self.__is_db_cache_loaded = False
        self.__mutex_db_cache_df = threading.Lock()

        self.stoprequest = threading.Event()
        return

    def join(self, timeout=None):
        lg.Log.critical(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Cache "' + str(self.cache_identifier) + '" join called..'
        )
        self.stoprequest.set()
        super(BaseDataCache, self).join(timeout=timeout)

    def is_loaded_from_db(self):
        return self.__is_db_cache_loaded

    #
    # Only when we need to get all data from cache.
    #
    def wait_for_data_loading(
            self,
            timeout_secs = 5.0
    ):
        sleep_time = 0.2
        total_time_sleep = 0.0
        while not self.__is_db_cache_loaded:
            if total_time_sleep >= timeout_secs:
                lg.Log.warning(
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Data cache "' + str(self.cache_identifier)
                    + '" not ready after ' + str(total_time_sleep) + 's.'
                )
                return False
            t.sleep(sleep_time)
            total_time_sleep += sleep_time

        return True

    #
    # Updates data frame containing Table rows
    #
    def update_cache(
            self,
            # New rows from DB
            db_rows,
            # mutex to lock df
            mutex
    ):
        if not self.__is_db_cache_loaded:
            return

        try:
            mutex.acquire()
            for row in db_rows:
                if type(row) is not dict:
                    raise Exception(
                        'Row to update is not dict type: ' + str(row)
                    )
                if self.db_table_id_name not in row.keys():
                    warnmsg = \
                        'Cache "' + str(self.cache_identifier)\
                        + '". Ignoring row because column table id name "' + str(self.db_table_id_name) \
                        + '" not found in row to update: ' + str(row) + '.'
                    lg.Log.warning(warnmsg)
                    continue

                id = row[self.db_table_id_name]
                self.__db_cache[id] = row
                self.__db_cache_last_update_time[id] = dt.datetime.now()
                lg.Log.info(
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Cache "' + str(self.cache_identifier) + '". Updated row id ' + str(id) + ': ' + str(row)
                )
        except Exception as ex:
            lg.Log.error(
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Cache "' + str(self.cache_identifier)
                + '". Exception occurred updating DB cache with rows ' + str(db_rows)
                +', exception msg: ' + str(ex) + '.'
            )
        finally:
            mutex.release()

    def is_data_expire(
            self,
            last_update_time
    ):
        now = dt.datetime.now()
        data_age_secs = prf.Profiling.get_time_dif(start=last_update_time, stop=now)

        lg.Log.debugdebug(
            '****** NOW=' + str(now) + ', LAST UPDATE TIME=' + str(last_update_time)
            + ', expire=' + str(data_age_secs) + ' secs.'
        )

        if data_age_secs > self.expire_secs:
            return True
        else:
            return False

    #
    # Overwrite this function if your DB Object has different method of calling
    #
    def get_row_by_id_from_db(
            self,
            table_id
    ):
        raise Exception(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Cache "' + str(self.cache_identifier)
            + '". Method get_row_by_id_from_db() must be overridden in Derived Class'
        )

    def get_all_data_keys(self):
        return list(self.__db_cache.keys())

    #
    # Get only from cache
    #
    def get_all_data_cache(self):
        all_data_from_cache = []
        try:
            self.__mutex_db_cache_df.acquire()
            for key in self.__db_cache.keys():
                all_data_from_cache.append(self.__db_cache[key].copy())
            return all_data_from_cache
        finally:
            self.__mutex_db_cache_df.release()

    #
    # By default, return value is always a list if "table_column_name" is None
    #
    def get_data(
            self,
            table_id,
            # If None, return the whole row
            table_column_name = None,
            # At times we may want to never use cache
            no_cache = False,
            # At times, when server is overloaded we may only want to use cache despite expiry
            use_only_cache_data = False
    ):
        # Try to convert, this might throw exception
        if type(table_id) is not int:
            try:
                table_id = int(table_id)
            except Exception as ex_int:
                errmsg = \
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                    + ': Cache "' + str(self.cache_identifier) + '" Table ID "' + str(table_id)\
                    + '" error. Get column "' + str(table_column_name) +'". Table ID should be integer type.'
                lg.Log.error(errmsg)
                return None

        # We keep data from cache if exists, in case query from data source fails
        data_from_cache = None
        try:
            self.__mutex_db_cache_df.acquire()
            if not no_cache:
                index_list = self.__db_cache.keys()
                if table_id in index_list:
                    # From cache is dict type
                    row = self.__db_cache[table_id]
                    last_update_time = self.__db_cache_last_update_time[table_id]

                    if table_column_name:
                        # Requested just column name
                        data_from_cache = row[table_column_name]
                    else:
                        # No column name, return entire row dict
                        data_from_cache = row

                    is_data_expired = self.is_data_expire(last_update_time=last_update_time)

                    if is_data_expired:
                        lg.Log.debug(
                            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Cache outdated, get table column "' + str(table_column_name)
                            + '" for table ID ' + str(table_id) + '.'
                        )

                    if use_only_cache_data or (not is_data_expired):
                        lg.Log.debug(
                            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Table Type from Cache: ' + str(row)
                        )
                        return data_from_cache
                else:
                    lg.Log.debug(
                        str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Table ID not in DB Cache, Get intent column "' + str(table_column_name)
                        + '" for table ID ' + str(table_id) + '.'
                    )
            else:
                lg.Log.debug(
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Cache "' + str(self.cache_identifier) + '" still not ready or no_cache=' + str(no_cache)
                    + ' flag set, get intent column "' + str(table_column_name)
                    + '" for table ID ' + str(table_id) + ' from DB...'
                )

            row_from_db = self.get_row_by_id_from_db(table_id=table_id)
            if row_from_db is None:
                warnmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                          + ': Query from DB is None, returning data from cache..'
                lg.Log.warning(warnmsg)
                return data_from_cache

            if type(row_from_db) is dict:
                warnmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                         + ': Expecting a list, but got dict type from DB rows for ' + str(table_id) \
                         + ', rows data: ' + str(row_from_db)
                lg.Log.warning(warnmsg)
                # Default return type is always list
                row_from_db = [row_from_db]

            if len(row_from_db) != 1:
                errmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': Expecting 1 row returned for table ID ' + str(table_id)\
                         + ', but got ' + str(row_from_db) + ' rows. Rows data: ' + str(row_from_db) \
                         + '. Returning data from cache..'
                lg.Log.error(errmsg)
                return data_from_cache

            if table_column_name:
                value = row_from_db[0][table_column_name]
            else:
                value = row_from_db[0]
        except Exception as ex:
            errmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception occured getting table id ' + str(table_id)\
                     + ', column name "' + str(table_column_name)\
                     + '. Exception message: ' + str(ex) + '.'
            lg.Log.critical(errmsg)
            raise Exception(errmsg)
        finally:
            self.__mutex_db_cache_df.release()

        if self.__is_db_cache_loaded:
            self.update_cache(
                db_rows    = row_from_db,
                mutex      = self.__mutex_db_cache_df
            )

        return value

    #
    # Get either from cache or DB (if cache expired or not found in cache)
    #
    def get(
            self,
            table_id,
            column_name = None,
            use_only_cache_data = False
    ):
        return self.get_data(
            table_id = table_id,
            table_column_name = column_name,
            use_only_cache_data = use_only_cache_data
        )

    #
    # Get from data source / DB
    #
    def get_all_data(self):
        raise Exception(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Cache "' + str(self.cache_identifier) + '". Method get_all_data() must be overridden in Derived Class.'
        )

    def run(self):
        lg.Log.critical(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': BaseDataCache "' + str(self.cache_identifier) + '" thread started..'
        )

        time_elapsed_modulo = 0

        while True:
            if self.stoprequest.isSet():
                lg.Log.critical(
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Stop request for cache ' + str(self.cache_identifier) + ' received. Break from loop...'
                )
                break

            if time_elapsed_modulo == 0:
                # Cache DB rows as is into data frame, no changes to the row
                try:
                    self.__mutex_db_cache_df.acquire()

                    rows = self.get_all_data()

                    lg.Log.debug(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Data Cache "' + str(self.cache_identifier) + '" got rows: ' + str(rows)
                    )
                    update_time = dt.datetime.now()

                    self.__db_cache = {}
                    self.__db_cache_last_update_time = {}
                    if type(rows) in [list, tuple]:
                        for row in rows:
                            id = row[self.db_table_id_name]
                            self.__db_cache[id] = row
                            self.__db_cache_last_update_time[id] = update_time

                    lg.Log.important(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': DB Cache "' + str(self.cache_identifier) + '" READY. Read '
                        + str(len(self.__db_cache.keys())) + ' rows.'
                    )
                    self.__is_db_cache_loaded = True
                except Exception as ex:
                    errmsg = \
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                        + ': Cache "' + str(self.cache_identifier) \
                        + '" Exception getting all data, exception message "' + str(ex) + '"'
                    lg.Log.error(errmsg)
                    raise Exception(errmsg)
                finally:
                    self.__mutex_db_cache_df.release()

            if self.reload_all_every_n_secs is None:
                lg.Log.important(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Cache "' + str(self.cache_identifier) + '" thread ended, not doing periodic reload of all data.'
                )
                break

            t.sleep(BaseDataCache.THREAD_SLEEP_TIME)
            time_elapsed_modulo += BaseDataCache.THREAD_SLEEP_TIME
            if time_elapsed_modulo > self.reload_all_every_n_secs:
                time_elapsed_modulo = 0

        lg.Log.critical(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Cache "' + str(self.cache_identifier) + '" DONE'
        )

        return


if __name__ == '__main__':
    class MyCache(BaseDataCache):
        def get_row_by_id_from_db(
                self,
                table_id
        ):
            return self.db_obj.get(id=table_id)

        def get_all_data(self):
            return self.db_obj.get()

    class MyDataObject:
        def get(self, id=None):
            all = [
                {'id': 111, 'value':str(dt.datetime.now())},
                {'id': 222, 'value':str(dt.datetime.now() + dt.timedelta(seconds=60))}
            ]
            if id is None:
                return all
            else:
                for d in all:
                    if d['id'] == id:
                        return [d]
                return None

    cache_identifier = 'my test cache'
    data_obj = MyDataObject()
    id_name = 'id'
    column_name = 'value'

    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_DEBUG_1

    obj = MyCache.get_singleton(
        DerivedClass = MyCache,
        cache_identifier = cache_identifier,
        db_obj = data_obj,
        db_table_id_name = id_name
    )
    obj2 = MyCache.get_singleton(
        DerivedClass = MyCache,
        cache_identifier = cache_identifier,
        db_obj = data_obj,
        db_table_id_name = id_name
    )
    obj3 = MyCache.get_singleton(
        DerivedClass = MyCache,
        cache_identifier = cache_identifier,
        db_obj = data_obj,
        db_table_id_name = id_name
    )

    print('Starting thread...')
    obj.start()
    while not obj.is_loaded_from_db():
        t.sleep(1)
        print('Not yet ready cache')
    print('READY')

    id = 333
    print('===================================================================================')
    print('================================== TEST WRONG ID ==================================')
    print('===================================================================================')
    print('DATA ROW: ' + str(obj.get(table_id=id)))
    print('DATA COLUMN: ' + str(obj.get(table_id=id, column_name=column_name)))

    id = 222
    print('===================================================================================')
    print('=========================== FIRST ROUND GETS FROM CACHE ===========================')
    print('===================================================================================')
    print('DATA ROW: ' + str(obj.get(table_id=id)))
    print('DATA COLUMN: ' + str(obj.get(table_id=id, column_name=column_name)))

    t.sleep(2)
    print('===================================================================================')
    print('============================ SECOND ROUND GETS FROM DB ============================')
    print('===================================================================================')
    # Second round gets from DB
    obj.expire_secs = 0
    print('DATA ROW: ' + str(obj.get(table_id=id)))
    print('DATA COLUMN: ' + str(obj.get(table_id=id, column_name=column_name)))

    t.sleep(2)
    print('===================================================================================')
    print('======================= THIRD ROUND FORCE TO GET FROM CACHE =======================')
    print('===================================================================================')
    # 3rd round force to get from cache
    obj.expire_secs = 0
    print('DATA ROW: ' + str(obj.get(table_id=id, use_only_cache_data=True)))
    print('DATA COLUMN: ' + str(obj.get(table_id=id, column_name=column_name, use_only_cache_data=True)))

    t.sleep(2)
    print('===================================================================================')
    print('============================ 4TH ROUND FORCE EXCEPTION ============================')
    print('===================================================================================')
    # 4th round to test assertion
    obj.expire_secs = 3600
    try:
        res = obj.get(table_id='abc')
        print('DATA: ' + str(res))
    except Exception as ex:
        print('Expecting exception...')
        print(ex)

    print('Stopping job...')
    BaseDataCache.stop_singleton_job(DerivedClass=MyCache, cache_identifier=cache_identifier)
    # obj.join(timeout=5)
    print('Done')
