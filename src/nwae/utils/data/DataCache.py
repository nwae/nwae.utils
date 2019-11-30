
import threading
import datetime as dt
import time as t
import nwae.utils.Profiling as prf
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


class DataCache(threading.Thread):

    THREAD_SLEEP_TIME = 5

    # 5 minutes default
    CACHE_EXPIRE_SECS = 5*60

    # Derived columns
    COL_LAST_UPDATE_TIME = '__lastUpdateTimeCache'

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
            if cache_identifier in DataCache.SINGLETON_OBJECT.keys():
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

    def __init__(
            self,
            cache_identifier,
            db_obj,
            db_table_id_name,
            expire_secs = CACHE_EXPIRE_SECS,
            # If None, means we reload all only once and quit thread
            reload_all_every_n_secs = None
    ):
        super(DataCache, self).__init__()

        self.cache_identifier = cache_identifier
        self.db_obj = db_obj
        self.db_table_id_name = db_table_id_name

        self.expire_secs = expire_secs
        self.reload_all_every_n_secs = reload_all_every_n_secs

        # Keep in a dict
        self.__db_cache = None
        self.__mutex_db_cache_df = threading.Lock()

        self.stoprequest = threading.Event()
        return

    def join(self, timeout=None):
        lg.Log.critical(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Cache "' + str(self.cache_identifier) + '" join called..'
        )
        self.stoprequest.set()
        super(DataCache, self).join(timeout=timeout)

    def is_loaded_from_db(self):
        return (self.__db_cache is not None)

    #
    # Updates data frame containing Table rows
    #
    def update_cache(
            self,
            # New rows from DB
            db_rows,
            # Our cache in Data Frame format, without modifying what we get from DB, just add last update column
            cache_obj,
            # mutex to lock df
            mutex
    ):
        if cache_obj is None:
            return

        try:
            mutex.acquire()
            for row in db_rows:
                row[DataCache.COL_LAST_UPDATE_TIME] = dt.datetime.now()
                key = row[self.db_table_id_name]
                cache_obj[key] = row
                lg.Log.info(
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Cache "' + str(self.cache_identifier) + '". Updated row ' + str(key) + ': ' + str(row)
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

        return cache_obj

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
            + ': Cache "' + str(self.cache_identifier) + '". This method must be overridden in Derived Class'
        )

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
            table_id = int(table_id)
        assert isinstance(table_id, int),\
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
            + ': Cache "' + str(self.cache_identifier)\
            + '". Get intent column "' + str(table_column_name) +'". Table ID should be integer type.'

        value = None
        try:
            self.__mutex_db_cache_df.acquire()
            if (self.__db_cache is not None) and (not no_cache):
                index_list = self.__db_cache.keys()
                if table_id in index_list:
                    row = self.__db_cache[table_id]
                    last_update_time = row[DataCache.COL_LAST_UPDATE_TIME]

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
                        # Just get the first row
                        if table_column_name:
                            return row[table_column_name]
                        else:
                            return row
                else:
                    lg.Log.debug(
                        str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Table ID not in DB Intent Cache, Get intent column "' + str(table_column_name)
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

            if len(row_from_db) != 1:
                errmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': Expecting 1 row returned for table ID ' + str(table_id)\
                         + ', but got ' + str(row_from_db) + ' rows. Rows data:\n\r' + str(row_from_db)
                lg.Log.critical(errmsg)
                raise Exception(errmsg)

            if table_column_name:
                value = row_from_db[0][table_column_name]
            else:
                value = row_from_db
        except Exception as ex:
            errmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception occured getting table id ' + str(table_id)\
                     + ', column name "' + str(table_column_name)\
                     + '. Exception message: ' + str(ex) + '.'
            lg.Log.critical(errmsg)
            raise Exception(errmsg)
        finally:
            self.__mutex_db_cache_df.release()

        if self.__db_cache is not None:
            self.__db_cache = self.update_cache(
                db_rows    = row_from_db,
                cache_obj  = self.__db_cache,
                mutex      = self.__mutex_db_cache_df
            )

        return value

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

    def run(self):
        lg.Log.critical(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': DataCache "' + str(self.cache_identifier) + '" thread started..'
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

                    rows = self.db_obj.get()
                    lg.Log.debug(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Data Cache "' + str(self.cache_identifier) + '" got rows: ' + str(rows)
                    )
                    update_time = dt.datetime.now()

                    self.__db_cache = {}
                    for row in rows:
                        id = row[self.db_table_id_name]
                        # Add a last update time to the data row
                        row[DataCache.COL_LAST_UPDATE_TIME] = update_time
                        self.__db_cache[id] = row

                    lg.Log.important(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': DB Cache "' + str(self.cache_identifier) + '" READY. Read'
                        + str(len(self.__db_cache.keys())) + ' rows.'
                    )
                except Exception as ex:
                    lg.Log.error(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Cache "' + str(self.cache_identifier)
                        + '" Exception getting all data, exception message "' + str(ex) + '"'
                    )
                finally:
                    self.__mutex_db_cache_df.release()

            if self.reload_all_every_n_secs is None:
                lg.Log.important(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Cache "' + str(cache_identifier) + '" thread ended, not doing periodic reload of all data.'
                )
                break

            t.sleep(DataCache.THREAD_SLEEP_TIME)
            time_elapsed_modulo += DataCache.THREAD_SLEEP_TIME
            if time_elapsed_modulo > self.reload_all_every_n_secs:
                time_elapsed_modulo = 0

        return


if __name__ == '__main__':
    class MyCache(DataCache):
        def get_row_by_id_from_db(
                self,
                table_id
        ):
            return self.db_obj.get(id=table_id)

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
    obj.join(timeout=5)
    print('Done')
