# -*- coding: utf-8 -*-

import os
import sys
import nwae.utils.StringUtils as su
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo
import datetime as dt
import threading
import re


#
# Base class for configs
#
class BaseConfig:

    PARAM_CONFIGFILE = 'configfile'

    SINGLETON = {}

    #
    # Always call this method only to make sure we get singleton
    #
    @staticmethod
    def get_cmdline_params_and_init_config_singleton(
            Derived_Class,
            default_config_file = None,
            obfuscate_passwords = False
    ):
        # Default values
        pv = {
            BaseConfig.PARAM_CONFIGFILE: default_config_file
        }

        # Config file on command line will overwrite default config file
        args = sys.argv
        for arg in args:
            arg_split = arg.split('=')
            if len(arg_split) == 2:
                param = arg_split[0].lower()
                value = su.StringUtils.trim(arg_split[1])
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
            obfuscate_passwords = obfuscate_passwords
        )
        return BaseConfig.SINGLETON[configfile]

    def get_config(self, param):
        if self.is_file_last_updated_time_is_newer():
            self.reload_config()
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
            ignore_non_existant_config_file = False,
            obfuscate_passwords = False
    ):
        self.config_file = config_file
        self.ignore_non_existant_config_file = ignore_non_existant_config_file
        self.obfuscate_passwords = obfuscate_passwords

        self.param_value = {}
        self.__mutex_reload_config = threading.Lock()
        self.file_updated_time = None

        #
        # This might throw exception
        #
        self.__check_file_existence()
        self.file_updated_time = os.path.getmtime(self.config_file)
        lg.Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Config file path "' + str(self.config_file) + '" ok, updated time "'
            + str(dt.datetime.fromtimestamp(self.file_updated_time).strftime('%Y%m%d %H:%M:%S'))
            + '".'
        )
        self.reload_config()
        return

    def __check_file_existence(self):
        if not os.path.isfile(self.config_file):
            errmsg = \
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                + ': Config file path "' + str(self.config_file) \
                + '" is not a valid file path!'
            lg.Log.warning(errmsg)
            if not self.ignore_non_existant_config_file:
                raise Exception(errmsg)
        else:
            lg.Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Config file path "' + str(self.config_file) + '" OK.'
            )

    def is_file_last_updated_time_is_newer(self):
        try:
            # Check if file time is newer
            ftime = os.path.getmtime(self.config_file)
            is_file_newer = (self.file_updated_time is None) or (ftime > self.file_updated_time)

            if is_file_newer:
                lg.Log.important(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Config file "' + str(self.config_file) + '" updated time "'
                    + str(dt.datetime.fromtimestamp(ftime).strftime('%Y%m%d %H:%M:%S'))
                    + '", is newer than "'
                    + str(dt.datetime.fromtimestamp(self.file_updated_time).strftime('%Y%m%d %H:%M:%S'))
                    + '".'
                )
                # Update with new time
                self.file_updated_time = ftime

            return is_file_newer
        except Exception as ex:
            errmsg = \
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                + ': Exception checking file updated time for config "' + str(self.config_file)\
                + '", exception message: ' + str(ex) + '.'
            if not self.ignore_non_existant_config_file:
                lg.Log.error(errmsg)
            return False

    def set_default_value_if_not_exist(
            self,
            param,
            default_value
    ):
        if param not in self.param_value.keys():
            self.param_value[param] = default_value
            lg.Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Not found param "' + str(param) + ' set to default value "' + str(default_value) + '".'
            )

    def convert_value_to_boolean_type(
            self,
            param
    ):
        if param not in self.param_value.keys():
            self.param_value[param] = False

        self.param_value[param] = str(self.param_value[param]).lower() in ['1', '1.0', 'yes', 'y', "true"]

        lg.Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Convert to boolean param "' + str(param)
            + '" set to "' + str(self.param_value[param]) + '".'
        )

    def convert_value_to_float_type(
            self,
            param,
            default_val
    ):
        if param not in self.param_value.keys():
            self.param_value[param] = default_val

        try:
            self.param_value[param] = float(self.param_value[param])
        except Exception as ex_float_conversion:
            lg.Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Failed to convert param "' + str(param) + '" value "' + str(self.param_value[param])
                + '" to float type, set to default value ' + str(default_val)
                + '. Exception message: ' + str(ex_float_conversion) + '.'
            )
            self.param_value[param] = default_val

        lg.Log.critical(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Convert to float param "' + str(param)
            + '" set to ' + str(self.param_value[param]) + '.'
        )

    def __obfuscate_passwords(
            self,
            param,
            value
    ):
        try:
            if self.obfuscate_passwords:
                if re.match(pattern='[a-zA-Z_\-]*(password|pwd|passwd)', string=param):
                    return '*****'
            return value
        except Exception as ex:
            lg.Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error obfuscate password param "' + str(param) + '", value "' + str(value) + '": ' + str(ex)
            )
            return value

    def reload_config(
            self
    ):
        try:
            lg.Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Config file "' + str(self.config_file) + '" reloading...'
            )

            self.__mutex_reload_config.acquire()

            # Param-Values
            tmp_param_value = {}

            f = open(self.config_file, 'r', encoding='utf-8')
            linelist_file = f.readlines()
            f.close()

            lg.Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Config file "' + str(self.config_file) + '" read successfully: '
                + str([self.__obfuscate_passwords(param=l, value=l) for l in linelist_file])
            )

            linelist = []
            for line in linelist_file:
                # Although trim() already removes ending newlines, explicitly removing them is no harm
                line = su.StringUtils.trim(su.StringUtils.remove_newline(line))
                # Ignore empty lines
                if line == '':
                    continue
                # Ignore comment lines
                if (line[0] == '#'):
                    continue
                linelist.append(line)

            for line in linelist:
                arg_split = line.split('=', maxsplit=1)
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
                        + ': Set param "' + str(param) + '" to "'
                        + str(self.__obfuscate_passwords(param=param, value=value)) + '"'
                    )

            self.param_value = tmp_param_value

            lg.Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Read from app config file "' + str(self.config_file)
                + ', file lines: ' + str([self.__obfuscate_passwords(param=l, value=l) for l in linelist])
                + ', properties: ' + str({k:self.__obfuscate_passwords(param=k, value=v) for k,v in self.param_value.items()})
            )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Error reading app config file "' + str(self.config_file)\
                     + '". Exception message ' + str(ex)
            if not self.ignore_non_existant_config_file:
                lg.Log.critical(errmsg)
                raise Exception(errmsg)
        finally:
            self.__mutex_reload_config.release()


if __name__ == '__main__':
    # config_file = '/usr/local/git/nwae/nwae/app.data/config/nwae.cf.local'
    import time
    cffile = '/usr/local/git/nwae/nwae.utils/app.data/config/sample.cf'
    obfuscate_pwd = True

    bconfig = BaseConfig.get_cmdline_params_and_init_config_singleton(
        Derived_Class = BaseConfig,
        default_config_file = cffile,
        obfuscate_passwords = obfuscate_pwd
    )
    bconfig2 = BaseConfig.get_cmdline_params_and_init_config_singleton(
        Derived_Class = BaseConfig,
        default_config_file = cffile,
        obfuscate_passwords = obfuscate_pwd
    )
    time.sleep(1)
    bconfig.reload_config()

    bconfig = BaseConfig(
        config_file = cffile,
        obfuscate_passwords = obfuscate_pwd
    )

    bconfig.reload_config()

    while True:
        time.sleep(1)
        print(bconfig.get_config(param='name'))
        # print(bconfig.get_config(param='abc'))
