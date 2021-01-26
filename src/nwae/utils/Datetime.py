# -*- coding: utf-8 -*-

from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


class Datetime:

    @staticmethod
    # Convert time unit to integer based on a reference date
    def count_months(
            # In datetime type
            x,
            ref_year = 2021,
            ref_month = 1,
            ref_day = 1
    ):
        assert type(x) in [datetime, pd.Timestamp]
        refdate = datetime(year=ref_year, month=ref_month, day=ref_day)
        dif_years = x.year - refdate.year
        dif_months = x.month - refdate.month
        return dif_years * 12 + dif_months

    @staticmethod
    # Convert time unit to integer based on a reference date
    def count_days(
            # In datetime type
            x,
            ref_year = 2021,
            ref_month = 1,
            ref_day = 1
    ):
        assert type(x) in [datetime, pd.Timestamp]
        refdate = datetime(year=ref_year, month=ref_month, day=ref_day)
        return Datetime.get_date_range(date_start=refdate, date_end=x, unit='day')

    @staticmethod
    def offset_date_by_day(
            d,
            n = 1
    ):
        assert type(d) is datetime
        return d + timedelta(n)

    @staticmethod
    def offset_date_by_month(
            d,
            n = 1
    ):
        assert type(d) is datetime
        day_original = d.day
        n_pos = abs(n)
        if n_pos != 0:
            n_sign = n / n_pos
        else:
            n_sign = 1
        # datetime type assigns by copy, so won't change original
        d_return = d
        for i in range(n_pos):
            if n_sign > 0:
                d_return = (d_return.replace(day=1) + timedelta(32)).replace(day=day_original)
            else:
                d_return = (d_return.replace(day=1) - timedelta(1)).replace(day=day_original)
        return d_return

    @staticmethod
    def get_date_range(
            date_start,
            date_end,
            # 'day', 'second'
            unit = 'day',
    ):
        assert type(date_start) in [datetime, pd.Timestamp],\
            'Type date start "' + str(type(date_start)) + '" must be datetime or pandas Timestamp'
        assert type(date_end) in [datetime, pd.Timestamp],\
            'Type date end "' + str(type(date_end)) + '" must be datetime or pandas Timestamp'
        range_date = date_end - date_start
        # Ignore microseconds and milliseconds
        secs_count = range_date.days*86400 + range_date.seconds + range_date.microseconds/1000000
        if unit == 'day':
            return np.round(secs_count/86400, 2)
        elif unit == 'second':
            return np.round(secs_count, 5)
        else:
            raise Exception(
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Unsupported unit "' + str(unit) + '"'
            )


if __name__ == '__main__':
    now = datetime.now()
    print(now)
    n = 5
    now_plus_offset = Datetime.offset_date_by_month(d=now, n=n)
    now_minus_offset = Datetime.offset_date_by_month(d=now, n=-n)
    print('+' + str(n) + ' months: ' + str(now_plus_offset))
    print('-' + str(n) +' months: ' + str(now_minus_offset))
    print(now)

    print('Count months "' + str(now) + '" = ' + str(Datetime.count_months(x=now)))
    print('Count months +' + str(n) + '  "' + str(now_plus_offset) + '" = ' + str(Datetime.count_months(x=now_plus_offset)))
    print('Count months -' + str(n) + '  "' + str(now_minus_offset) + '" = ' + str(Datetime.count_months(x=now_minus_offset)))

    d_end = datetime.now()
    d_start = d_end.replace(hour=0)
    diff_secs = Datetime.get_date_range(date_start=d_start, date_end=d_end, unit='second')
    diff_days = Datetime.get_date_range(date_start=d_start, date_end=d_end, unit='day')
    print(
        'For d1 "' + str(d_start) + '", d2 "' + str(d_end)
        + '", diff time in seconds = ' + str(diff_secs)
        + ', diff time in days = ' + str(diff_days)
    )

    res = Datetime.count_days(x=now, ref_year=2020, ref_month=1, ref_day=1)
    print('Number of day count for "' + str(now) + '" = ' + str(res))
    exit(0)
