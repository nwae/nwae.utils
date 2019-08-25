
import base64
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


class Encode:

    @staticmethod
    def encode_base64(
            s,
            encoding = 'utf-8'
    ):
        try:
            b = base64.b64encode(s = str(s).encode(encoding))
            s_base64 = b.decode(encoding)
            return s_base64
        except Exception as ex:
            errmsg = str(Encode.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ' Cannot encode string "' + str(s) + '" to base64. Exception "'\
                     + str(ex) + '.'
            lg.Log.error(errmsg)
            raise Exception(errmsg)

    @staticmethod
    def decode_base64(
            s_base64,
            encoding = 'utf-8'
    ):
        try:
            b = base64.b64decode(s = s_base64)
            s = b.decode(encoding)
            return s
        except Exception as ex:
            errmsg = str(Encode.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ' Cannot decode base64 string "' + str(s_base64) + '". Exception "'\
                     + str(ex) + '.'
            lg.Log.error(errmsg)
            raise Exception(errmsg)


if __name__ == '__main__':
    s_base64 = Encode.encode_base64('String to encode to base 64')
    print(s_base64)
    s = Encode.decode_base64(s_base64)
    print(s)