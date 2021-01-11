# -*- coding: utf-8 -*-

from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from datetime import datetime, timedelta


class Datetime:

    @staticmethod
    # Convert time unit to integer
    def count_months(
            # In datetime type
            x,
            ref_year = 2021,
            ref_month = 1,
            ref_day = 1
    ):
        refdate = datetime(year=ref_year, month=ref_month, day=ref_day)
        dif_years = x.year - refdate.year
        dif_months = x.month - refdate.month
        return dif_years * 12 + dif_months

    @staticmethod
    def offset_date_by_month(
            d,
            n = 1
    ):
        assert type(d) is datetime
        day_original = d.day
        n_pos = abs(n)
        n_sign = n / n_pos
        # datetime type assigns by copy, so won't change original
        d_return = d
        for i in range(n_pos):
            if n_sign > 0:
                d_return = (d_return.replace(day=1) + timedelta(32)).replace(day=day_original)
            else:
                d_return = (d_return.replace(day=1) - timedelta(1)).replace(day=day_original)
        return d_return


if __name__ == '__main__':
    now = datetime.now()
    print(now)
    n = 5
    now_plus_offset = Datetime.offset_date_by_month(d=now, n=n)
    now_minus_offset = Datetime.offset_date_by_month(d=now, n=-n)
    print('+5 months: ' + str(now_plus_offset))
    print('-5 months: ' + str(now_minus_offset))
    print(now)

    print('Count months "' + str(now) + '" = ' + str(Datetime.count_months(x=now)))
    print('Count months +5 "' + str(now_plus_offset) + '" = ' + str(Datetime.count_months(x=now_plus_offset)))
    print('Count months -5 "' + str(now_minus_offset) + '" = ' + str(Datetime.count_months(x=now_minus_offset)))
    exit(0)