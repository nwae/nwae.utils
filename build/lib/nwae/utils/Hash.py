# -*- coding: utf-8 -*-

import hashlib
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
import numpy as np
import nwae.utils.UnitTest as ut


class Hash:

    STR_ENCODING = 'utf-8'

    ALGO_SHA1 = 'sha1'
    ALGO_SHA256 = 'sha256'
    ALGO_SHA512 = 'sha512'
    ALGO_SHA3_256 = 'sha3_256'
    ALGO_SHA3_512 = 'sha3_512'
    ALGO_LIST = [
        ALGO_SHA1, ALGO_SHA256, ALGO_SHA512, ALGO_SHA3_256, ALGO_SHA3_512
    ]

    BLOCK_CHINESE    = (0x4e00, 0x9fff) # CJK Unified Ideographs
    BLOCK_KOREAN_SYL = (0xAC00, 0xD7AF) # Korean syllable block

    def __init__(self):
        return

    @staticmethod
    def hash(
            string,
            algo = ALGO_SHA1
    ):
        str_encode = string.encode(encoding = Hash.STR_ENCODING)
        try:
            if algo == Hash.ALGO_SHA1:
                h = hashlib.sha1(str_encode)
            elif algo == Hash.ALGO_SHA256:
                h = hashlib.sha256(str_encode)
            elif algo == Hash.ALGO_SHA512:
                h = hashlib.sha512(str_encode)
            elif algo == Hash.ALGO_SHA3_256:
                h = hashlib.sha3_256(str_encode)
            elif algo == Hash.ALGO_SHA3_512:
                h = hashlib.sha3_512(str_encode)
            else:
                raise Exception('Unsupported hash algo "' + str(algo) + '".')
            return h.hexdigest()
        except Exception as ex:
            errmsg = str(__name__) + ' ' + str() \
                     + 'Error hashing string "' + str(string) + '" using algo "' + str(algo)\
                     + '". Exception: ' + str(ex)
            Log.error(errmsg)
            return None

    @staticmethod
    def convert_ascii_string_to_other_alphabet(
            ascii_char_string,
            # Default to CJK Unicode Block
            unicode_range = BLOCK_CHINESE,
            # If the characters come from a hexdigest from a hash, we can compress 4 times,
            # otherwise for a random ascii string, we can only compress 2 characters to 1 chinese.
            group_n_char = 2
    ):
        uni_len = unicode_range[1] - unicode_range[0] + 1

        r = len(ascii_char_string) % 4
        if r != 0:
            # Append 0's
             ascii_char_string = ascii_char_string + '0'*(4-r)
            # raise Exception('Hash length ' + str(len(hash_hex_string))
            #                 + ' for "' + str(hash_hex_string) + '" not 0 modulo-4')

        hash_zh = ''

        len_block = int( len(ascii_char_string) / group_n_char )
        for i in range(0, len_block, 1):
            idx_start = group_n_char*i
            idx_end = idx_start + group_n_char
            s = ascii_char_string[idx_start:idx_end]

            # Convert to Chinese, Korean, etc
            if group_n_char == 2:
                ord_arr = np.array([ord(x) for x in s])
                val = ord_arr * np.array([2 ** (8 * (x - 1)) for x in range(len(ord_arr), 0, -1)])
                val = np.sum(val)
                Log.debug(
                    'Index start=' + str(idx_start) + ', end=' + str(idx_end) + ', s=' + str(s)
                    + ', ordinal=' + str(ord_arr) + ', val=' + str(hex(val))
                )
                cjk_unicode = ( val % uni_len ) + unicode_range[0]
                hash_zh += chr(cjk_unicode)
            elif group_n_char == 4:
                Log.debug(
                    'Index start=' + str(idx_start) + ', end=' + str(idx_end) + ', s=' + str(s)
                )
                n = int('0x' + str(s), 16)
                cjk_unicode = ( n % uni_len ) + unicode_range[0]
                hash_zh += chr(cjk_unicode)
                Log.debugdebug(
                    'From ' + str(idx_start) + ': ' + str(s)
                    + ', n=' + str(n) + ', char=' + str(chr(cjk_unicode))
                )

        return hash_zh


class HashUnitTest:
    def __init__(self, ut_params):
        return

    def run_unit_test(self):
        res_final = ut.ResultObj(count_ok=0, count_fail=0)

        s = '니는 먹고 싶어'
        tests_set_1 = [
            [Hash.ALGO_SHA1,
             '蔮膫圈嫩慁覕邜蹋妡狿'],
            [Hash.ALGO_SHA256,
             '葶杊閹翔綐僤徼戻髯鼚胦嘭藃诠灑浽'],
            [Hash.ALGO_SHA512,
             '詐鏙仟墍例嵝烐檦蝡溲薑珇鸦東燢爻纷欜陲囚劚攠菜槑茹輀濯偑袁蓣质簨'],
            [Hash.ALGO_SHA3_256,
             '厥驹踸鸨揱澯鑢擠鳰僸覑儽悃徵絨控'],
            [Hash.ALGO_SHA3_512,
             '醜怅僒础衺菼惓隔鮚腋釔晞鏙屜咖龩檵因伖蘦惌灱騾凊纅弪鮾蕏解铦欪臓']
        ]
        for x in tests_set_1:
            algo = x[0]
            expected = x[1]
            # In Linux command line, echo -n "$s" | shasum -a 1 (or 256,512)
            Log.debug('Using algo "' + str(algo) + '":')
            hstr = Hash.hash(string=s, algo=algo)
            Log.debug('Hash: ' + str(hstr))
            observed = Hash.convert_ascii_string_to_other_alphabet(
                ascii_char_string = hstr,
                # unicode_range   = Hash.BLOCK_KOREAN_SYL,
                group_n_char      = 4
            )
            res_final.update_bool(res_bool=ut.UnitTest.assert_true(
                observed = observed,
                expected = expected,
                test_comment = 'test string "' + str(hstr) + '" got "' + str(observed) + '"'
            ))

        tests_set_2 = [
            ['abc/ii{}.!&%[][\\+=', '嵢弯敩睽簡琥坝坜礽縰'],
            ['8829amsf)(*&^%^*./', '蘸耹嵭潦眨砦娥娪簯縰']
        ]
        for x in tests_set_2:
            ascii_string = x[0]
            expected = x[1]
            observed = Hash.convert_ascii_string_to_other_alphabet(
                ascii_char_string = ascii_string
            )
            res_final.update_bool(res_bool=ut.UnitTest.assert_true(
                observed = observed,
                expected = expected,
                test_comment = 'test string "' + str(ascii_string) + '" got "' + str(observed) + '"'
            ))

        return res_final


if __name__ == '__main__':
    Log.LOGLEVEL = Log.LOG_LEVEL_DEBUG_1
    exit(HashUnitTest(ut_params=None).run_unit_test().count_fail)
