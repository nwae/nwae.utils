# -*- coding: utf-8 -*-

import nwae.utils.Log as lg


class UnitTestParams:
    def __init__(
            self,
            dirpath_wordlist     = None,
            postfix_wordlist     = None,
            dirpath_app_wordlist = None,
            postfix_app_wordlist = None,
            dirpath_synonymlist  = None,
            postfix_synonymlist  = None,
            dirpath_model        = None
    ):
        self.dirpath_wordlist = dirpath_wordlist
        self.postfix_wordlist = postfix_wordlist
        self.dirpath_app_wordlist = dirpath_app_wordlist
        self.postfix_app_wordlist = postfix_app_wordlist
        self.dirpath_synonymlist = dirpath_synonymlist
        self.postfix_synonymlist = postfix_synonymlist
        self.dirpath_model = dirpath_model

    def to_string(self):
        return 'Dir Wordlist "' + str(self.dirpath_wordlist)\
               + '", Postfix Wordlist "' + str(self.postfix_wordlist)\
               + '", Dir App Wordlist "' + str(self.dirpath_app_wordlist)\
               + '", Postfix App Wordlist "' + str(self.postfix_app_wordlist)\
               + '", Dir Synonym List "' + str(self.dirpath_synonymlist)\
               + '", Postfix Synonym List "' + str(self.postfix_synonymlist)\
               + '", Dir Model "' + str(self.dirpath_model) + '"'

class ResultObj:
    def __init__(self, count_ok, count_fail):
        self.count_ok = count_ok
        self.count_fail = count_fail

class UnitTest:

    def __init__(self):
        return

    def run_unit_test(self):
        print(str(self.__class__) + ': Fake unit test..')
        return ResultObj(count_ok=0, count_fail=0)

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

        return ResultObj(
            count_ok   = count_ok,
            count_fail = count_fail
        )


if __name__ == '__main__':
    res = UnitTest().run_unit_test()
    exit(res.count_fail)

