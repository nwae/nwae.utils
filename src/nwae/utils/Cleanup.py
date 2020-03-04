# -*- coding: utf-8 -*-

import os
import datetime as dt
import time
import re
import sys
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


class Cleanup:

    # Default to 7 day
    MAX_AGE_SECS = 7.0*24*60*60

    def __init__(
            self,
            folder,
            regex,
            max_age_secs = MAX_AGE_SECS
    ):
        self.folder = folder
        self.regex = regex
        self.max_age_secs = max_age_secs
        if not os.path.isdir(self.folder):
            raise Exception('Path "' + str(self.folder) + '" is not a directory!')
        return

    def remove_old_files(
            self
    ):
        tnow = time.time()
        tnow_str = format(dt.datetime.fromtimestamp(tnow))
        lg.Log.debug(
            str(self.__class__) + str(getframeinfo(currentframe()).lineno)
            + ': Removing old files from folder "' + self.folder + '" older than '
            + str(self.max_age_secs) + ' secs...'
        )
        try:
            farr = os.listdir(self.folder)
            lg.Log.debug('Files in folder: ' + str(farr))
            for file in farr:
                if not re.search(pattern=self.regex, string=file):
                    # lg.Log.info('Ignoring file "' + str(file) + '", not matching regex "' + str(self.regex) + '".')
                    continue
                updated_time = os.path.getmtime(self.folder + '/' + file)
                updated_time_str = format(dt.datetime.fromtimestamp(updated_time))
                age_secs = tnow - updated_time

                lg.Log.debug(
                    'Checking file "' + str(file) + '"..'
                    + '" last updated time ' + str(updated_time_str)
                    + ', age ' + str(round(age_secs/86400,2)) + ' days ('
                    + str(round(age_secs,0)) + ' secs).'
                )

                if age_secs > self.max_age_secs:
                    os.remove(self.folder + '/' + file)
                    lg.Log.important(
                        str(self.__class__) + str(getframeinfo(currentframe()).lineno)
                        +': File "' + str(file) + '" removed, aged '
                        + str(round(age_secs/86400,2)) + ' days ('
                        + str(round(age_secs,0)) + 's)'
                    )
        except Exception as ex:
            errmsg = str(self.__class__) + str(getframeinfo(currentframe()).lineno)\
                     + ': Error removing old files from folder "' + str(self.folder)\
                     + '". Exception message ' + str(ex) + '.'
            lg.Log.error(errmsg)


if __name__ == '__main__':
    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_INFO

    command_line_params = {
        'folder': None,
        'regex': None,
        'maxage': Cleanup.MAX_AGE_SECS
    }
    args = sys.argv

    for arg in args:
        arg_split = arg.split('=')
        if len(arg_split) == 2:
            param = arg_split[0].lower()
            value = arg_split[1]
            if param in list(command_line_params.keys()):
                command_line_params[param] = value

    cleaner = Cleanup(
        folder = command_line_params['folder'],
        regex  = command_line_params['regex'],
        #regex  = '(^chatid.)|(.state$)',
        max_age_secs = float(command_line_params['maxage'])
    )
    cleaner.remove_old_files()