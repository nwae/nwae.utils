from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from datetime import datetime
import re
from nwae.utils.StringUtils import StringUtils
import numpy as np
import pandas as pd


class DataPreprocessor:

    DEFAULT_NAN_STRING = 'NULL'
    # If true means in place of empty value in dataframe (null/nan), will be a string such as "NULL"
    DEFAULT_FINAL_OUTPUT_AS_STRING_NOT_NAN = True

    @staticmethod
    def trim_lower(x):
        x = StringUtils.trim(str(x))
        return x.lower()

    @staticmethod
    def slice_str(x, maxlen):
        len_x = len(str(x))
        l = min(len_x, maxlen)
        if l < len_x:
            x_slice = str(x)[0:l]
            Log.warning(
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Cut from length ' + str(len_x) + ' to ' + str(maxlen)
                + ' characters. From "' + str(x) + '" to "' + str(x_slice) + '"'
            )
            return x_slice
        else:
            return x

    @staticmethod
    def to_datetime_format(x, format='%Y-%m-%d %H:%M:%S.%f', remove_last_n_chars=0):
        try:
            if remove_last_n_chars > 0:
                x = x[0:-remove_last_n_chars]
            # print('***** x=' + str(x))
            if type(x) is pd._libs.tslibs.timestamps.Timestamp:
                # Convert to string, then only convert back to datetime
                return datetime.strptime(datetime.strftime(x, format), format)
            else:
                return datetime.strptime(x, format)
        except Exception as ex:
            raise Exception(
                'Date string "' + str(x) + '" failed to convert to datetime: ' + str(ex)
            )

    # Convert datetime to convenient number
    @staticmethod
    def date_to_number(
            # datetime object
            x,
            round_to_integer = False,
            # If relative date is given, total days from this date is returned
            relative_date = None
    ):
        if relative_date is None:
            n = x.year * 10000 + x.month * 100 + x.day
            if round_to_integer:
                return n
            else:
                return (
                        n + (x.hour * 3600 + x.minute * 60 + x.second) / 86400
                )
        else:
            date_diff = x - relative_date
            n = date_diff.days + date_diff.seconds/86400 + date_diff.microseconds/(86400*1000000)
            if round_to_integer:
                n = round(n)
            return n

    #
    # Add new datetime number (datetime converted to number) column
    # Важное примечание: в таком случае, формат отображения в датафрейме будет зависеть от pandas-а, так как
    # даты уже сталы типом datetime и больше не типом string
    #
    @staticmethod
    def convert_datetime_to_number(
            x,
            datetime_format,
            round_to_integer = False,
            # If relative date is given, total days from this date is returned
            relative_date = None
    ):
        try:
            if type(x) is str:
                dtime = datetime.strptime(str(x), datetime_format)
            else:
                dtime = x
            dtime_no = DataPreprocessor.date_to_number(
                x                = dtime,
                round_to_integer = round_to_integer,
                relative_date    = relative_date
            )
            return dtime_no
        except Exception as ex:
            Log.error(
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error converting "' + str(x) + '" type "' + str(type(x)) + '": ' + str(ex)
            )
            return 0

    # Filter out non-number characters
    @staticmethod
    def filter_number(x):
        x = str(x)
        # Replace anything not in the characters list with ''
        x = re.sub(pattern='[^0-9e.-]', repl='', string=x)
        if x == '':
            x = 0
        return float(x)

    #
    # For nan values, we will replace with a string like "NULL", so that mergings will not exclude them.
    #
    @staticmethod
    def clean_nan_values(
            data,
            colnames,
            nan_string = DEFAULT_NAN_STRING
    ):
        # MUST convert column to string, so all NAs, N/As become string
        for name in colnames:
            # Create new copy
            col_series = np.array(data[name])
            condition_null = np.array(data[name].isnull())
            # Count nan rows
            count_nan = np.sum(condition_null * 1)
            Log.important(
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Total ' + str(name) + ' rows with NULL = ' + str(count_nan)
            )
            # Replace nan
            col_series[condition_null] = nan_string
            data[name] = col_series.astype(dtype=str)
        return data

    @staticmethod
    def put_back_nan_values(
            data,
            colnames,
            nan_string = DEFAULT_NAN_STRING
    ):
        # After merging, we can now put back the nan
        for colname in colnames:
            is_null_values = data[colname] == nan_string
            data[colname][is_null_values] = np.nan


if __name__ == '__main__':
    x = DataPreprocessor.to_datetime_format(
        x = '2020-08-09 18:45:00.123',
        format = '%Y-%m-%d %H:%M:%S.%f',
        remove_last_n_chars = 0
    )
    print(x)