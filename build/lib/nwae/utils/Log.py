# -*- coding: utf-8 -*-

import datetime as dt
import time
import nwae.utils.StringUtils as su
import os


class Log:

    #
    # Log Levels
    #
    LOG_LEVEL_CRITICAL  = 0.0
    LOG_LEVEL_ERROR     = 1.0
    LOG_LEVEL_WARNING   = 2.0
    LOG_LEVEL_IMPORTANT = 2.5
    # Standard level logging
    LOG_LEVEL_INFO      = 3.0
    LOG_LEVEL_DEBUG_1   = 4.0
    # Almost as good as stepping through the code
    LOG_LEVEL_DEBUG_2   = 5.0

    # Variables
    LOGFILE = ''
    LOGLEVEL = LOG_LEVEL_INFO
    DEBUG_PRINT_ALL_TO_SCREEN = False
    IS_LOG_TO_VARIABLE_LIST = False

    def __init__(self):
        return

    @staticmethod
    def set_path(logfile_path):
        Log.LOGFILE = logfile_path

    @staticmethod
    def critical(
            s,
            encoding='utf-8',
            log_list=None
    ):
        Log.do_log_level(level=Log.LOG_LEVEL_CRITICAL, s=s, encoding=encoding, log_list=log_list)

    @staticmethod
    def error(
            s,
            encoding='utf-8',
            log_list=None
    ):
        Log.do_log_level(level=Log.LOG_LEVEL_ERROR, s=s, encoding=encoding, log_list=log_list)

    @staticmethod
    def warning(
            s,
            encoding='utf-8',
            log_list=None
    ):
        Log.do_log_level(level=Log.LOG_LEVEL_WARNING, s=s, encoding=encoding, log_list=log_list)

    @staticmethod
    def important(
            s,
            encoding='utf-8',
            log_list=None
    ):
        Log.do_log_level(level=Log.LOG_LEVEL_IMPORTANT, s=s, encoding=encoding, log_list=log_list)

    @staticmethod
    def info(
            s,
            encoding='utf-8',
            log_list=None
    ):
        Log.do_log_level(level=Log.LOG_LEVEL_INFO, s=s, encoding=encoding, log_list=log_list)

    @staticmethod
    def debug(
            s,
            encoding='utf-8',
            log_list=None
    ):
        Log.do_log_level(level=Log.LOG_LEVEL_DEBUG_1, s=s, encoding=encoding, log_list=log_list)

    @staticmethod
    def debugdebug(
            s,
            encoding='utf-8',
            log_list=None
    ):
        Log.do_log_level(level=Log.LOG_LEVEL_DEBUG_2, s=s, encoding=encoding, log_list=log_list)

    @staticmethod
    def get_level_string_prefix(level):
        if level == Log.LOG_LEVEL_CRITICAL:
            return 'CRITICAL'
        elif level == Log.LOG_LEVEL_ERROR:
            return 'ERROR'
        elif level == Log.LOG_LEVEL_WARNING:
            return 'WARNING'
        elif level == Log.LOG_LEVEL_IMPORTANT:
            return 'IMPORTANT'
        elif level == Log.LOG_LEVEL_INFO:
            return 'INFO'
        elif level == Log.LOG_LEVEL_DEBUG_1:
            return 'DEBUG'
        elif level == Log.LOG_LEVEL_DEBUG_2:
            return 'DEBUGDEBUG'
        else:
            return ''

    @staticmethod
    def do_log_level(
            level,
            s,
            encoding = 'utf-8',
            log_list = None
    ):
        if Log.LOGLEVEL >= level:
            prefix = Log.get_level_string_prefix(level=level)
            logmsg = str(prefix) + ': ' + str(s)
            Log.log(
                s = logmsg,
                encoding = encoding,
                log_list = log_list
            )

    @staticmethod
    def log(
            s,
            encoding = 'utf-8',
            # Append log here if type is list
            log_list = None
    ):
        if s is None:
            return

        is_log_to_variable_list = (type(log_list) is list)

        # Because sometimes we just dump whole objects to log
        s = str(s)

        s = su.StringUtils.trim(str=s)
        if len(s) == 0:
            return

        timestamp = dt.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

        if is_log_to_variable_list:
            log_list.append(timestamp + ': ' + s)

        if Log.LOGFILE == '' or Log.DEBUG_PRINT_ALL_TO_SCREEN:
            print(timestamp + ': ' + s)
            return

        # Prefix for log file as today's date so it won't grow too big
        ymd = dt.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
        logfile_name_today_date_prefix = Log.LOGFILE + '.' + ymd

        try:
            f = None
            if os.path.isfile(logfile_name_today_date_prefix):
                f = open(file=logfile_name_today_date_prefix, mode='a', encoding=encoding)
            else:
                f = open(file=logfile_name_today_date_prefix, mode='w', encoding=encoding)

            f.write(timestamp + ': ' + s + '\n')
            f.close()
        except Exception as ex:
            errmsg = 'Log file [' + logfile_name_today_date_prefix\
                     + '] don''t exist!. Exception message "' + str(ex)
            print(errmsg)
            raise Exception(errmsg)


if __name__ == '__main__':
    Log.info('Test log info...')