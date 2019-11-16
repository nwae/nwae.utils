# -*- coding: utf-8 -*-

import nwae.utils.Log as lg


class UnitTest:

    @staticmethod
    def get_unit_test_result(
            input_x,
            result_test,
            result_expected,
    ):
        assert len(input_x) == len(result_test)
        assert len(result_test) == len(result_expected)

        count_ok = 0
        count_fail = 0
        for i in range(len(result_test)):
            x = input_x[i]
            res_t = result_test[i]
            res_e = result_expected[i]
            ok = (res_t == res_e)
            count_ok += 1*ok
            count_fail += 1*(not ok)
            if not ok:
                lg.Log.warning(
                    'FAILED "' + str(x) + '", expected "' + str(res_e) + '", got "' + str(res_t) + '"'
                )
            else:
                lg.Log.info(
                    'OK "' + str(x) + '". Output "' + str(res_t) + '"'
                )

        class retc:
            def __init__(
                    self,
                    count_ok,
                    count_fail
            ):
                self.count_ok = count_ok
                self.count_fail = count_fail

        return retc(
            count_ok   = count_ok,
            count_fail = count_fail
        )

