# -*- coding: utf-8 -*-

import hashlib
from nwae.utils.Log import Log


class Hash:

    STR_ENCODING = 'utf-8'

    def __init__(self):
        return

    @staticmethod
    def hash(
            string,
            algo = 'sha512'
    ):
        str_encode = string.encode(encoding = Hash.STR_ENCODING)
        try:
            if algo == 'sha1':
                h = hashlib.sha1(str_encode)
            elif algo == 'sha256':
                h = hashlib.sha256(str_encode)
            elif algo == 'sha512':
                h = hashlib.sha512(str_encode)
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
    # In Linux command line, echo -n "$s" | shasum -a 1
    print(Hash.hash(string=s, algo='sha1'))
    # In Linux command line, echo -n "$s" | shasum -a 256
    print(Hash.hash(string=s, algo='sha256'))
    # In Linux command line, echo -n "$s" | shasum -a 512
    print(Hash.hash(string=s, algo='sha512'))
