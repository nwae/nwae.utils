# -*- coding: utf-8 -*-

import hashlib
from nwae.utils.Log import Log


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
            errmsg = 'Error hashing string "' + str(string) + '" using algo "' + str(algo)\
                     + '". Exception: ' + str(ex)
            Log.error(errmsg)
            return None


if __name__ == '__main__':
    s = '니는 먹고 싶어'
    for algo in Hash.ALGO_LIST:
        # In Linux command line, echo -n "$s" | shasum -a 1 (or 256,512)
        print('Using algo "' + str(algo) + '":')
        print(Hash.hash(string=s, algo=algo))
