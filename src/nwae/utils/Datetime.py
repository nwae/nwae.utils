# -*- coding: utf-8 -*-

from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from datetime import datetime, timedelta


class Datetime:

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
    n = 13
    print('+13 months: ' + str(Datetime.offset_date_by_month(d=now, n=n)))
    print('-13 months: ' + str(Datetime.offset_date_by_month(d=now, n=-n)))
    print(now)
    exit(0)
