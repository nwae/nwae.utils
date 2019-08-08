
import threading
import datetime as dt
import time as t
import mozg.common.util.Log as lg
import mozg.common.data.IntentCategory as dbintcat
import mozg.common.data.Intent as dbint
import mozg.common.data.IntentAnswer as dbintans
import mozg.common.data.IntentTraining as dbinttr
import mozg.common.data.Bot as dbbot
import mozg.common.util.Profiling as prf
import pandas as pd
import mozg.common.data.security.Auth as au
import mozg.common.data.security.AuthConfig as authcfg
from inspect import currentframe, getframeinfo


class DbIntentCache(threading.Thread):

    THREAD_SLEEP_TIME = 5

    # Keys of the intent cache
    KEY_CACHE_INTENTS_LAST_UPDATE = 'lastUpdatedTime'
    KEY_CACHE_INTENTS_INTENT_ANSWERS = 'intentAnswers'
    # 5 minutes default
    CACHE_EXPIRE_SECS = 5*60

    COL_INTENT         = 'Intent'
    COL_INTENT_ID      = 'Intent ID'    # Derived column, joining Category + Intent
    # Can be "system" (ignore), "regex" (regular expression type), "user" (what we want)
    COL_INTENT_TYPE    = 'Intent Type'
    COL_WEIGHT         = 'Weight'
    COL_ANSWER         = 'Answer'
    # Derived columns
    COL_INTENT_FULL_PATH = 'intentPath'
    COL_LAST_UPDATE_TIME = 'lastUpdateTimeCache'
    COL_REGEX = 'regex'

    # Singletons
    SINGLETON_OBJECT = {}
    SINGLETON_OBJECT_MUTEX = threading.Lock()

    @staticmethod
    def get_singleton(
            db_profile,
            account_id,
            bot_id,
            bot_lang,
            cache_intent_name = True,
            cache_intent_answers = False,
            cache_intent_regex = False,
            cache_expiry_time_secs = CACHE_EXPIRE_SECS
    ):
        DbIntentCache.SINGLETON_OBJECT_MUTEX.acquire()

        botkey = dbbot.Bot.get_bot_key(
            db_profile = db_profile,
            account_id = account_id,
            bot_id     = bot_id,
            lang       = bot_lang
        )

        try:
            if botkey in DbIntentCache.SINGLETON_OBJECT.keys():
                if DbIntentCache.SINGLETON_OBJECT[botkey] is not None:
                    lg.Log.important(str(DbIntentCache.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                     + ': Returning existing singleton object for db cache for botkey "' + str(botkey) + '".')
                    return DbIntentCache.SINGLETON_OBJECT[botkey]
            # Create new instance
            singleton = DbIntentCache(
                db_profile    = db_profile,
                account_id    = account_id,
                bot_id        = bot_id,
                cache_intent  = cache_intent_name,
                cache_answers = cache_intent_answers,
                cache_regex   = cache_intent_regex
            )
            # Don't start until called to start
            # singleton.start()
            DbIntentCache.SINGLETON_OBJECT[botkey] = singleton
            lg.Log.important(str(DbIntentCache.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                             + ': Created new singleton object for db cache for botkey "' + str(botkey) + '".')
            return DbIntentCache.SINGLETON_OBJECT[botkey]
        except Exception as ex:
            errmsg = str(DbIntentCache.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception occurred getting singleton object for botkey "' + str(botkey)\
                     + '". Exception message: ' + str(ex) + '.'
            lg.Log.critical(errmsg)
            raise Exception(errmsg)
        finally:
            DbIntentCache.SINGLETON_OBJECT_MUTEX.release()

    #
    # Start the singleton job separately, so we make sure we only start when everything
    # is already ok. Otherwise, these threads will start for nothing and load the CPU.
    #
    def start_singleton_job(botkey):
        DbIntentCache.SINGLETON_OBJECT_MUTEX.acquire()

        try:
            DbIntentCache.SINGLETON_OBJECT[botkey].start()
        except Exception as ex:
            errmsg = str(DbIntentCache.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception starting singleton object for botkey "' + str(botkey)\
                     + '". Exception message: ' + str(ex) + '.'
            lg.Log.critical(errmsg)
        finally:
            DbIntentCache.SINGLETON_OBJECT_MUTEX.release()

    def __init__(
            self,
            db_profile,
            account_id,
            bot_id,
            # By default will cache intent names
            cache_intent  = True,
            # By default will not cache intent answers
            cache_answers = False,
            cache_regex = False,
            expire_secs   = CACHE_EXPIRE_SECS
    ):
        super(DbIntentCache, self).__init__()

        if db_profile not in authcfg.AuthConfig.AUTH_PROFILES.keys():
            raise Exception('No such authentication profile [' + str(db_profile) + ']')

        self.db_profile = db_profile

        self.account_id = account_id
        self.bot_id = bot_id

        # Intent names
        self.cache_intent = cache_intent
        self.cache_answers = cache_answers
        self.cache_regex = cache_regex

        self.expire_secs = expire_secs

        #
        # Keep in a data frame, the same row format returned from DB. Example:
        #      intentId    intentName     intentType regex        lastUpdateTime
        #        13         welcome         system  None      2019-07-17 11:48:05.558849
        #        14         noanswer        system  None      2019-07-17 11:48:05.558849
        #        15        网页切换语言       None    None      2019-07-17 11:48:05.558849
        #        16       PT 捕鱼王游戏未派彩   None    None      2019-07-17 11:48:05.558849
        #        17     清除谷歌浏览器缓存- 苹果/平板设备   None  None       2019-07-17 11:48:05.558849
        #        917          Bet ID        regex  "betid_\d.*_\d*"   2019-07-17 11:48:05.558849
        #
        # Don't do any processing on the rows returned from DB.
        # That is why we still keep the above DataFrame containers, where we append and remove
        # from container what we get from DB directly.
        #
        self.__db_cache_intent_df = None
        self.__mutex_db_cache_intent_df = threading.Lock()
        self.__db_cache_intent_cat_df = None
        self.__mutex_db_cache_intent_cat_df = threading.Lock()

        self.db_auth = au.Auth(
            auth_profile = self.db_profile
        )

        # Initialize DB objects
        self.db_int = dbint.Intent(
            db_profile = self.db_profile,
            bot_id     = self.bot_id
        )
        self.db_int_cat = dbintcat.IntentCategory(
            db_profile = self.db_profile
        )

        # Regex intents are always refreshed in this class thread
        self.__regex_intents = None
        self.__regex_intents_mutex = threading.Lock()

        self.stoprequest = threading.Event()
        return

    def join(self, timeout=None):
        lg.Log.critical(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                   + ': Join called..')
        self.stoprequest.set()
        super(DbIntentCache, self).join(timeout=timeout)

    def is_loaded_from_db(self):
        return (self.__db_cache_intent_df is not None)

    #
    # Do minimal things here, don't modify what we get from DB at all preferably
    #
    def convert_db_rows_to_dataframe(
            self,
            db_rows,
            index_name
    ):
        try:
            # Convert list to data frame
            df_tmp = pd.DataFrame(db_rows)

            # Add column of last update time
            df_tmp[DbIntentCache.COL_LAST_UPDATE_TIME] = dt.datetime.now()

            # Set index to answer ID
            df_tmp = df_tmp.set_index([index_name])
            return df_tmp
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Error converting DB intent row\n\r' + str(db_rows)\
                     + '\n\rException is "' + str(ex) + '".'
            lg.Log.warning(errmsg)
            raise Exception(errmsg)

    #
    # Updates data frame containing Intent Table rows
    #
    def update_cache(
            self,
            # New Intent rows from DB
            db_rows,
            # Our cache in Data Frame format, without modifying what we get from DB, just add last update column
            df,
            # Usually intentId column
            index_name,
            # mutex to lock df
            mutex
    ):
        if df is None:
            return

        try:
            mutex.acquire()
            # Convert DB returned rows to data frame with minimal processing
            df_tmp = self.convert_db_rows_to_dataframe(
                db_rows    = db_rows,
                index_name = index_name
            )

            # TODO Compare old/new data, no need to update if both are the same

            # Delete the rows
            indexes_to_delete = df_tmp.index.tolist()
            lg.Log.debug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                         + ': Rows to delete from cache: ' + str(indexes_to_delete))
            df = df.drop(indexes_to_delete)
            # Add new rows
            df = df.append(df_tmp, sort=False)
            lg.Log.debug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                         + ': Successfully appended rows to cache: ' + str(df_tmp.transpose().to_dict()))
        except Exception as ex:
            lg.Log.critical(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                       + ': Exception occurred updating DB cache with rows ' + str(db_rows)
                            +', exception msg: ' + str(ex))
        finally:
            mutex.release()

        return df

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

    def get_intent_column(
            self,
            intent_id,
            intent_column_name,
            # At times we may want to never use cache
            no_cache = False,
            # At times, when server is overloaded we may only want to use cache despite expiry
            use_only_cache_data = False
    ):
        # Try to convert, this might throw exception
        if type(intent_id) is not int:
            intent_id = int(intent_id)
        assert isinstance(intent_id, int),\
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
            +': Get intent column "' + str(intent_column_name) +'". Intent ID should be integer type.'

        value = None
        try:
            self.__mutex_db_cache_intent_df.acquire()
            if (self.__db_cache_intent_df is not None) and (not no_cache):
                if intent_id in self.__db_cache_intent_df.index:
                    # By taking .loc[] of the data frame, this actually returns a pandas Series
                    df = self.__db_cache_intent_df.loc[intent_id]
                    last_update_time = df[DbIntentCache.COL_LAST_UPDATE_TIME]

                    is_data_expired = self.is_data_expire(last_update_time=last_update_time)

                    if is_data_expired:
                        lg.Log.debug(
                            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                            + ': Cache outdated, get intent column "' + str(intent_column_name)
                            + '" for intent ID ' + str(intent_id) + '.'
                        )

                    if use_only_cache_data or (not is_data_expired):
                        lg.Log.debug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                     + ': Intent Type from Cache:\n\r' + str(df))
                        # Just get the first row
                        return df[intent_column_name]
                else:
                    lg.Log.debug(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Intent ID not in DB Intent Cache, Get intent column "' + str(intent_column_name)
                        + '" for intent ID ' + str(intent_id) + '.'
                    )
            else:
                lg.Log.debug(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Cache still not ready or no_cache=' + str(no_cache)
                    + ' flag set, get intent column "' + str(intent_column_name)
                    + '" for intent ID ' + str(intent_id) + ' from DB...'
                )

            rows = self.db_int.get(intentId=intent_id)
            if len(rows) != 1:
                errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': Expecting 1 row returned for intent ID ' + str(intent_id)\
                         + ', but got ' + str(rows) + ' rows. Rows data:\n\r' + str(rows)
                lg.Log.critical(errmsg)
                raise Exception(errmsg)

            value = rows[0][intent_column_name]
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception occured getting intent id ' + str(intent_id)\
                     + ', column name "' + str(intent_column_name)\
                     + '. Exception message: ' + str(ex) + '.'
            lg.Log.critical(errmsg)
            raise Exception(errmsg)
        finally:
            self.__mutex_db_cache_intent_df.release()

        # Update the intent cache
        if self.__db_cache_intent_df is not None:
            self.__db_cache_intent_df = self.update_cache(
                db_rows    = rows,
                df         = self.__db_cache_intent_df,
                index_name = self.__db_cache_intent_df.index.name,
                mutex      = self.__mutex_db_cache_intent_df
            )

        return value

    def get_intent_type(
            self,
            intent_id,
            use_only_cache_data=False
    ):
        return self.get_intent_column(
            intent_id           = intent_id,
            intent_column_name  = dbint.Intent.COL_INTENT_TYPE,
            use_only_cache_data = use_only_cache_data
        )

    def get_intent_name(
            self,
            intent_id,
            use_only_cache_data=False
    ):
        return self.get_intent_column(
            intent_id           = intent_id,
            intent_column_name  = dbint.Intent.COL_INTENT_NAME,
            use_only_cache_data = use_only_cache_data
        )

    def get_intent_require_authentication(
            self,
            intent_id,
            use_only_cache_data=False
    ):
        return self.get_intent_column(
            intent_id           = intent_id,
            intent_column_name  = dbint.Intent.COL_REQUIRE_AUTH,
            use_only_cache_data = use_only_cache_data
        )

    def get_replies(
            self,
            intent_id,
            use_only_cache_data=False
    ):
        list_answers = self.get_intent_column(
            intent_id           = intent_id,
            intent_column_name  = dbint.Intent.COL_INTENT_ANSWERS,
            no_cache            = not self.cache_answers,
            use_only_cache_data = use_only_cache_data
        )
        if len(list_answers) > 0:
            df = self.convert_db_rows_to_dataframe(
                db_rows    = list_answers,
                index_name = dbintans.IntentAnswer.COL_INTENT_ANSWER_ID
            )
        else:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': No replies for intent ID ' + str(intent_id) + ', bot id ' + str(self.bot_id) + ' found!'
            )

        return df

    #
    # TODO Regex should be in intent table, not in training data?
    #
    def get_intent_regex(
            self,
            intent_id,
            use_only_cache_data=False
    ):
        zhonglei = self.get_intent_type(intent_id=intent_id)

        # If not type regex, return None
        if zhonglei != dbint.Intent.ATTR_INTENT_TYPE_REGEX:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Intent ID ' + str(intent_id) + ' is not regex type!'
            )

        df_training = self.get_intent_column(
            intent_id           = intent_id,
            intent_column_name  = dbint.Intent.COL_INTENT_TRAININGS,
            use_only_cache_data = use_only_cache_data
        )

        # Extract first training data sentence
        regex = str(df_training[0][dbinttr.IntentTraining.COL_SENTENCE])
        return regex

    def __form_regex_intents_dataframe(
            self,
            db_rows
    ):
        ret_df = pd.DataFrame()
        for row in db_rows:
            intid = row[dbint.Intent.COL_INTENT_ID]
            intname = row[dbint.Intent.COL_INTENT_NAME]
            inttype = row[dbint.Intent.COL_INTENT_TYPE]
            int_trainings = row[dbint.Intent.COL_INTENT_TRAININGS]

            if len(int_trainings) > 0:
                regex = str(int_trainings[0][dbinttr.IntentTraining.COL_SENTENCE])
                ret_df = ret_df.append(
                    pd.DataFrame({
                        dbint.Intent.COL_INTENT_ID: [intid],
                        dbint.Intent.COL_INTENT_NAME: [intname],
                        dbint.Intent.COL_INTENT_TYPE: [inttype],
                        DbIntentCache.COL_REGEX: [regex]
                    }),
                    ignore_index=True
                )
        if ret_df.shape[0] > 0:
            ret_df.set_index([dbint.Intent.COL_INTENT_ID], inplace=True)

        return ret_df

    #
    # This is never fetched from DB, only from cache
    #
    def __get_regex_intents_from_db(
            self
    ):
        # Won't work if we get intent by type because all None types will also come back from the intents
        # So we keep under the intent category "/__regex" hardcoded
        # Get category id for "/__regex" folder
        row_intcat = self.db_int_cat.get(
            botId              = self.bot_id,
            intentCategoryName = self.db_int_cat.REGEX_DIRECTORY_RESERVED_NAME
        )
        lg.Log.debug('REGEX CATEGORY ID ROW:\n\r' + str(row_intcat))
        regex_intcat_id = row_intcat[0][dbintcat.IntentCategory.COL_INTENT_CATEGORY_ID]

        # Already the correct bot id
        db_rows = self.db_int.get(
            intentCategoryId = regex_intcat_id
        )
        lg.Log.debug('REGEX CATEGORY INTENTS FROM DB:\n\r' + str(db_rows))

        df_rows = self.__form_regex_intents_dataframe(db_rows=db_rows)

        lg.Log.debug('REGEX INTENTS DATAFRAME FOR BOT ' + str(self.bot_id) + ':\n\r' + str(df_rows))
        return df_rows

    def get_regex_intents(
            self,
            no_cache = False,
            use_only_cache_data = False
    ):
        # This variable should always be updated regularly by our thread
        if (not no_cache) and (type(self.__regex_intents) is pd.DataFrame):
            # Don't return reference object
            lg.Log.debug('**** RETURN REGEX INTENTS FROM CACHE:\n\r' + str(self.__regex_intents.copy()))
            return self.__regex_intents
        else:
            lg.Log.debug('**** RETURN REGEX INTENTS FROM DB..')
            return self.__get_regex_intents_from_db()

    def get_system_intent_id(
            self,
            system_intent_category,
            use_only_cache_data = False
    ):
        return self.db_int.get_system_intent_id(system_intent_category=system_intent_category)

    def __merge_intent_df_with_intent_category_df(
            self,
            df_intent
    ):
        if self.__db_cache_intent_cat_df is not None:
            return pd.merge(
                left     = df_intent,
                right    = self.__db_cache_intent_cat_df,
                on       = [dbint.Intent.COL_INTENT_CATEGORY_ID],
                how      = 'left',
                suffixes = ['', '_cat_table']
            )
        else:
            return None

    def run(self):
        lg.Log.critical(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                   + ': Thread started..')

        load_all = True
        count_sleep = 0

        # Reload regex intents every 1 minute for now, minimum 2 sleep rounds
        regex_count_sleep_required = max(2, int(60 / DbIntentCache.THREAD_SLEEP_TIME))

        while True:
            if self.stoprequest.isSet():
                lg.Log.critical(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Stop request for db intent cache bot id ' + str(self.bot_id) + ' received. Break from loop...'
                )
                break

            if load_all:
                # Load all only 1 time
                load_all = False

                try:
                    self.db_int.initialize_system_intents()
                except Exception as ex:
                    errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                             + ': Cannot initialize system intents. ' + str(ex)
                    lg.Log.error(errmsg)

                #
                # Get everything in one go
                #
                # Cache DB rows as is into data frame, no changes to the row
                try:
                    self.__mutex_db_cache_intent_df.acquire()
                    self.__mutex_db_cache_intent_cat_df.acquire()

                    rows_intent_cat = self.db_int_cat.get(botId=self.bot_id)
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Fetched ' + str(len(rows_intent_cat)) + ' categories from intentCategory table.'
                    )
                    self.__db_cache_intent_cat_df = pd.DataFrame(rows_intent_cat)
                    lg.Log.debugdebug(self.__db_cache_intent_cat_df[0:10])

                    rows_intent = self.db_int.get()
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Fetched ' + str(len(rows_intent)) + ' intents from intent table.'
                    )

                    self.__db_cache_intent_df = pd.DataFrame(rows_intent)
                    self.__db_cache_intent_df = self.__merge_intent_df_with_intent_category_df(
                        df_intent = self.__db_cache_intent_df
                    )
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Total intent rows ' + str(self.__db_cache_intent_df.shape) + ' for all bots.'
                    )

                    # Keep those with our bot ID only
                    self.__db_cache_intent_df = self.__db_cache_intent_df[
                        self.__db_cache_intent_df[dbintcat.IntentCategory.COL_BOT_ID] == int(self.bot_id)
                    ]
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Filtered Total intent rows ' + str(self.__db_cache_intent_df.shape)
                        + ' for all Bot ID ' + str(self.bot_id) + '.'
                    )

                    self.__db_cache_intent_df[DbIntentCache.COL_LAST_UPDATE_TIME] = dt.datetime.now()
                    self.__db_cache_intent_df.set_index([dbint.Intent.COL_INTENT_ID], inplace=True)

                    lg.Log.debugdebug(self.__db_cache_intent_df.columns)
                    lg.Log.debugdebug(self.__db_cache_intent_df[0:10].values)
                    lg.Log.debugdebug(self.__db_cache_intent_df[
                                          self.__db_cache_intent_df[dbint.Intent.COL_INTENT_TYPE]==
                                          dbint.Intent.ATTR_INTENT_TYPE_REGEX]
                                      )
                except Exception as ex:
                    lg.Log.error(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Exception getting all intents, exception message "' + str(ex) + '"'
                    )
                finally:
                    self.__mutex_db_cache_intent_cat_df.release()
                    self.__mutex_db_cache_intent_df.release()

            if self.cache_regex and (count_sleep == 0):
                # Refresh REGEX Intents
                # Always get from DB (no_cache=True)
                try:
                    tmp = self.get_regex_intents(no_cache=True)

                    self.__regex_intents_mutex.acquire()
                    self.__regex_intents = tmp
                    lg.Log.info(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Bot ID ' + str(self.bot_id) + ' regex intents refreshed from DB\n\r' + str(self.__regex_intents)
                    )
                except Exception as ex:
                    lg.Log.critical(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Failed to refresh regex intents from DB for bot id ' + str(self.bot_id)
                        + '. Exception message: ' + str(ex) + '.'
                    )
                finally:
                    if self.__regex_intents_mutex.locked():
                        self.__regex_intents_mutex.release()

            t.sleep(DbIntentCache.THREAD_SLEEP_TIME)
            count_sleep = (count_sleep + 1) % regex_count_sleep_required

        return


if __name__ == '__main__':
    au.Auth.init_instances()

    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_DEBUG_1

    obj = DbIntentCache.get_singleton(
        db_profile = 'mario2',
        account_id = 4,
        bot_id = 22,
        bot_lang = 'cn'
    )
    obj2 = DbIntentCache.get_singleton(
        db_profile = 'mario2',
        account_id = 4,
        bot_id = 22,
        bot_lang = 'cn'
    )
    obj3 = DbIntentCache.get_singleton(
        db_profile = 'mario2',
        account_id = 4,
        bot_id = 22,
        bot_lang = 'cn'
    )

    print('Starting thread...')
    obj.start()
    while not obj.is_loaded_from_db():
        t.sleep(5)
        print('Not yet ready cache')

    iid = 743
    iname = 'Bet ID'

    print('===================================================================================')
    print('=========================== FIRST ROUND GETS FROM CACHE ===========================')
    print('===================================================================================')
    print('REGEX INTENTS (from DB):\n\r' + str(obj.get_regex_intents(no_cache=True)))
    print('REGEX INTENTS (from cache):\n\r' + str(obj.get_regex_intents(no_cache=False)))

    # First round gets from cache
    res = obj.get_replies(intent_id=iid)
    print('REPLIES: ' + str(res.transpose().to_dict()))
    res = obj.get_intent_type(intent_id=iid)
    print('INTENT TYPE: ' + str(res))
    res = obj.get_intent_name(intent_id=iid)
    print('INTENT NAME: ' + str(res))
    res = obj.get_intent_regex(intent_id=iid)
    print('INTENT REGEX: "' + str(res) + '"')

    t.sleep(2)
    print('===================================================================================')
    print('============================ SECOND ROUND GETS FROM DB ============================')
    print('===================================================================================')
    # Second round gets from DB
    obj.expire_secs = 0
    res = obj.get_replies(intent_id=iid)
    print('REPLIES: ' + str(res.transpose().to_dict()))
    res = obj.get_intent_type(intent_id=iid)
    print('INTENT TYPE: ' + str(res))
    res = obj.get_intent_name(intent_id=iid)
    print('INTENT NAME: ' + str(res))
    res = obj.get_intent_regex(intent_id=iid)
    print('INTENT REGEX: "' + str(res) + '"')

    t.sleep(2)
    print('===================================================================================')
    print('======================= THIRD ROUND FORCE TO GET FROM CACHE =======================')
    print('===================================================================================')
    # 3rd round force to get from cache
    obj.expire_secs = 0
    res = obj.get_replies(intent_id=iid, use_only_cache_data=True)
    print('REPLIES: ' + str(res.transpose().to_dict()))
    res = obj.get_intent_type(intent_id=iid, use_only_cache_data=True)
    print('INTENT TYPE: ' + str(res))
    res = obj.get_intent_name(intent_id=iid, use_only_cache_data=True)
    print('INTENT NAME: ' + str(res))
    res = obj.get_intent_regex(intent_id=iid, use_only_cache_data=True)
    print('INTENT REGEX: "' + str(res) + '"')

    t.sleep(2)
    print('===================================================================================')
    print('============================ 4TH ROUND FORCE EXCEPTION ============================')
    print('===================================================================================')
    # 4th round to test assertion
    obj.expire_secs = 3600
    try:
        res = obj.get_replies(intent_id=iid)
        print('REPLIES: ' + str(res.transpose().to_dict()))
        res = obj.get_intent_type(intent_id=iid)
        print('INTENT TYPE: ' + str(res))
        res = obj.get_intent_name(intent_id=iid)
        print('INTENT NAME: ' + str(res))
        res = obj.get_intent_regex(intent_id=iid)
        print('INTENT REGEX: "' + str(res) + '"')
    except Exception as ex:
        print('Expecting exception...')
        print(ex)

    print('REGEX INTENTS:\n\r' + str(obj.get_regex_intents(no_cache=False)))
    t.sleep(60)

    print('Stopping job...')
    obj.join(timeout=5)
    print('Done')
