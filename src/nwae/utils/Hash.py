# -*- coding: utf-8 -*-

import hashlib
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe


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
    def convert_hash_to_char(
            hash_hex_string,
            # Default to CJK Unicode Block
            unicode_range = BLOCK_CHINESE
    ):
        uni_len = unicode_range[1] - unicode_range[0] + 1

        if len(hash_hex_string)%4 != 0:
            raise Exception('Hash length ' + str(len(hash_hex_string))
                            + ' for "' + str(hash_hex_string) + '" not 0 modulo-4')

        hash_zh = ''
        len_block = int( len(hash_hex_string) / 4 )
        for i in range(0, len_block, 1):
            idx_start = 4*i
            idx_end = idx_start + 4
            s = hash_hex_string[idx_start:idx_end]
            # Convert to Chinese
            n = int('0x' + str(s), 16)
            cjk_unicode = ( n % uni_len ) + unicode_range[0]
            hash_zh += chr(cjk_unicode)
            Log.debugdebug(
                'From ' + str(idx_start) + ': ' + str(s)
                + ', n=' + str(n) + ', char=' + str(chr(cjk_unicode))
            )

        return hash_zh


if __name__ == '__main__':
    s = '니는 먹고 싶어'
    for algo in Hash.ALGO_LIST:
        # In Linux command line, echo -n "$s" | shasum -a 1 (or 256,512)
        print('Using algo "' + str(algo) + '":')
        hstr = Hash.hash(string=s, algo=algo)
        print(hstr)
        hstr_cn = Hash.convert_hash_to_char(
            hash_hex_string = hstr,
            # unicode_range   = Hash.BLOCK_KOREAN_SYL
        )
        print(hstr_cn)
