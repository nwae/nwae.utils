# -*- coding: utf-8 -*-

import os
import sys
import nwae.utils.StringUtils as su
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


#
# Base class for configs
#
class BaseConfig:

    PARAM_CONFIGFILE = 'configfile'

    DEFAULT_LOGLEVEL = lg.Log.LOG_LEVEL_INFO

    SINGLETON = None

    #
    # Always call this method only to make sure we get singleton
    #
    @staticmethod
    def get_cmdline_params_and_init_config_singleton():
        if type(BaseConfig.SINGLETON) is BaseConfig:
            lg.Log.info(
                str(BaseConfig.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Config Singleton from file "' + str(BaseConfig.SINGLETON.CONFIGFILE)
                + '" exists. Returning Singleton..'
            )
            return BaseConfig.SINGLETON

        # Default values
        pv = {
            'configfile': None
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
            raise Exception('"configfile" param not found on command line!')

        #
        # !!!MOST IMPORTANT, top directory, otherwise all other config/NLP/training/etc. files we won't be able to find
        #
        BaseConfig.SINGLETON = BaseConfig(
            config_file = pv[BaseConfig.PARAM_CONFIGFILE]
        )
        return BaseConfig.SINGLETON

    def __getattr__(self, item):
        if item in self.__dict__.keys():
            return self.__dict__[item]
        else:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': No such attribute "' + str(item) + '"'
            )

    def get_config(self, param):
        if param in self.param_value.keys():
            return self.param_value[param]
        else:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': No such config param "' + str(param) + '"'
            )

    def __init__(
            self,
            config_file
    ):
        # Param-Values
        self.param_value = {}

        self.param_value[BaseConfig.PARAM_CONFIGFILE] = config_file
        if not os.path.isfile(self.get_config(param=BaseConfig.PARAM_CONFIGFILE)):
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Configfile "' + str(self.get_config(param=BaseConfig.PARAM_CONFIGFILE))
                + '" is not a valid file path!'
            )

        try:
            f = open(config_file, 'r')
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
                    self.param_value[param] = value
                    lg.Log.important(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Set param "' + str(param) + '" to "' + str(value) + '"'
                    )

            lg.Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Read from app config file "' + str(config_file)
                + ', file lines:\n\r' + str(linelist) + ', properties\n\r' + str(self.param_value)
            )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Error reading app config file "' + str(config_file)\
                     + '". Exception message ' + str(ex)
            lg.Log.critical(errmsg)
            raise Exception(errmsg)


if __name__ == '__main__':
    bconfig = BaseConfig(
        config_file = '/usr/local/git/nwae/nwae/app.data/config/nwae.cf.local'
    )
