# -*- coding: utf-8 -*-

import os
import sys
import nwae.utils.StringUtils as su
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo
import datetime as dt
import threading


#
# Base class for configs
#
class BaseConfig:

    PARAM_CONFIGFILE = 'configfile'

    DEFAULT_RELOAD_EVERY_X_SECS = 300

    SINGLETON = {}

    #
    # Always call this method only to make sure we get singleton
    #
    @staticmethod
    def get_cmdline_params_and_init_config_singleton(
            Derived_Class,
            reload_every_x_secs = DEFAULT_RELOAD_EVERY_X_SECS
    ):
        # Default values
        pv = {
            BaseConfig.PARAM_CONFIGFILE: None
        }
        args = sys.argv

        for arg in args:
            arg_split = arg.split('=')
            if len(arg_split) == 2:
                param = arg_split[0].lower()
                value = arg_split[1]
                if param in list(pv.keys()):
                    pv[param] = value

        if pv[BaseConfig.PARAM_CONFIGFILE] is None:
            raise Exception('"' + str(BaseConfig.PARAM_CONFIGFILE) + '" param not found on command line!')

        configfile = pv[BaseConfig.PARAM_CONFIGFILE]
        if configfile in BaseConfig.SINGLETON.keys():
            lg.Log.info(
                str(BaseConfig.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Config Singleton from file "' + str(configfile)
                + '" exists. Returning Singleton..'
            )
            return Derived_Class.SINGLETON[configfile]

        #
        # Instantiate the Derived Class, not this base config
        #
        BaseConfig.SINGLETON[configfile] = Derived_Class(
            config_file         = configfile,
            reload_every_x_secs = reload_every_x_secs
        )
        return BaseConfig.SINGLETON[configfile]

    def get_config(self, param):
        if param in self.param_value.keys():
            return self.param_value[param]
        else:
            errmsg =\
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                + ': No such config param "' + str(param) + '"'
            lg.Log.warning(errmsg)
            return None

    def __init__(
            self,
            config_file,
            reload_every_x_secs = DEFAULT_RELOAD_EVERY_X_SECS
    ):
        self.config_file = config_file
        self.last_updated_time = None
        self.reload_every_x_secs = reload_every_x_secs

        self.param_value = {}

        self.__mutex_reload_config = threading.Lock()
        self.reload_config()

    def set_default_value_if_not_exist(
            self,
            param,
            default_value
    ):
        if param not in self.param_value.keys():
            self.param_value[param] = default_value
            lg.Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Param "' + str(param) + ' do not exist, set to default value "' + str(default_value) + '".'
            )

    def reload_config(
            self
    ):
        tnow = dt.datetime.now()

        if self.last_updated_time is not None:
            tdif = tnow - self.last_updated_time
            #
            # Not yet expired, no need to reload
            #
            if tdif.total_seconds() <= self.reload_every_x_secs:
                lg.Log.info(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Not yet expired ' + str(tdif.total_seconds()) + ' <= ' + str(self.reload_every_x_secs) + '.'
                )
                return

        if not os.path.isfile(self.config_file):
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Config file path "' + str(self.config_file)
                + '" is not a valid file path!'
            )
        else:
            lg.Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Config file path "' + str(self.config_file) + '" OK.'
            )

        try:
            self.__mutex_reload_config.acquire()
            # Param-Values
            tmp_param_value = {}

            f = open(self.config_file, 'r')
            linelist_file = f.readlines()
            f.close()

            linelist = []
            for line in linelist_file:
                line = su.StringUtils.trim(su.StringUtils.remove_newline(line))
                # Ignore comment lines, empty lines
                if (line[0] == '#') or (line == ''):
                    continue
                linelist.append(line)

            for line in linelist:
                arg_split = line.split('=')
                lg.Log.debugdebug(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Read line "' + str(line) + '", split to ' + str(arg_split)
                )
                if len(arg_split) == 2:
                    # Standardize to lower
                    param = su.StringUtils.trim(arg_split[0].lower())
                    value = su.StringUtils.trim(arg_split[1])
                    tmp_param_value[param] = value
                    lg.Log.important(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Set param "' + str(param) + '" to "' + str(value) + '"'
                    )

            self.last_updated_time = dt.datetime.now()
            self.param_value = tmp_param_value

            lg.Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Read from app config file "' + str(self.config_file)
                + ', file lines:\n\r' + str(linelist) + ', properties\n\r' + str(self.param_value)
            )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Error reading app config file "' + str(self.config_file)\
                     + '". Exception message ' + str(ex)
            lg.Log.critical(errmsg)
            raise Exception(errmsg)
        finally:
            self.__mutex_reload_config.release()


if __name__ == '__main__':
    # config_file = '/usr/local/git/nwae/nwae/app.data/config/nwae.cf.local'
    import time
    bconfig = BaseConfig.get_cmdline_params_and_init_config_singleton(
        reload_every_x_secs = 2
    )
    bconfig2 = BaseConfig.get_cmdline_params_and_init_config_singleton()
    time.sleep(1)
    bconfig.reload_config()
    time.sleep(1.1)
    bconfig.reload_config()

    bconfig = BaseConfig(
        config_file = '/usr/local/git/nwae/nwae/app.data/config/nwae.cf.local',
        reload_every_x_secs = 5
    )

    time.sleep(2)
    bconfig.reload_config()

    time.sleep(4)
    bconfig.reload_config()

    print(bconfig.get_config(param='topdir'))
    print(bconfig.get_config(param='abc'))
