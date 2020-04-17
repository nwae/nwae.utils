# -*- coding: utf-8 -*-

import os
import random
# pip install pycryptodome
from Crypto.Cipher import AES
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from base64 import b64encode, b64decode
import nwae.utils.UnitTest as ut


STR_ENCODING = 'utf-8'


class AES_Encrypt:

    AES_MODE_EAX = 'aes.eax'
    AES_MODE_CBC = 'aes.cbc'

    #
    # Return object when encrypting
    #
    class EncryptRetClass:
        def __init__(
                self,
                cipher_mode,
                ciphertext_b64,
                plaintext_b64,
                tag_b64,
                nonce_b64
        ):
            self.cipher_mode = cipher_mode
            self.ciphertext_b64 = ciphertext_b64
            self.plaintext_b64 = plaintext_b64
            self.tag_b64 = tag_b64
            self.nonce_b64 = nonce_b64

    DEFAULT_BLOCK_SIZE_AES_CBC = 16
    SIZE_NONCE = 16

    CHARS_STR = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' \
        + 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфцчшщъыьэюя' \
        + 'ㅂㅈㄷㄱ쇼ㅕㅑㅐㅔㅁㄴㅇㄹ호ㅓㅏㅣㅋㅌㅊ퓨ㅜㅡㅃㅉㄸㄲ쑈ㅕㅑㅒㅖㅁㄴㅇㄹ호ㅓㅏㅣㅋㅌㅊ퓨ㅜㅡ' \
        + 'ๅ/_ภถุึคตจขชๆไำพะัีรนยฟหกดเ้่าสผปแอิืท+๑๒๓๔ู฿๕๖๗๘๙๐ฎฑธ' \
        + '1234567890' \
        + '`~!@#$%^&*()_+-=[]\{}|[]\\;\':",./<>?'

    @staticmethod
    def generate_random_bytes(size = 16, printable = False):
        if not printable:
            return os.urandom(size)
        else:
            rs = ''.join(random.choice(AES_Encrypt.CHARS_STR) for i in range(size))
            return bytes(rs.encode(encoding=STR_ENCODING))[0:size]

    def __init__(
            self,
            # 16 or 32 byte key
            key,
            nonce = None,
            mode = AES_MODE_EAX,
            text_encoding = 'utf-8'
    ):
        self.key = key
        Log.debug('Using key ' + str(str(self.key)) + '. Size = ' + str(len(self.key)) + '.')
        self.cipher_mode_str = mode
        if self.cipher_mode_str == AES_Encrypt.AES_MODE_EAX:
            self.cipher_mode = AES.MODE_EAX
        elif self.cipher_mode_str == AES_Encrypt.AES_MODE_CBC:
            self.cipher_mode = AES.MODE_CBC
        else:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Unsupported AES mode "' + str(self.cipher_mode_str) + '"'
            )
        if nonce is None:
            # Must be 16 bytes
            # nonce = key[0:16]
            nonce = AES_Encrypt.generate_random_bytes(size=AES_Encrypt.SIZE_NONCE, printable=True)

        self.nonce = nonce
        Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Using nonce "' + str(self.nonce) + '". Size = ' + str(len(self.nonce))
        )

        self.text_encoding = text_encoding
        return

    def encode(
            self,
            # bytes format
            data
    ):
        try:
            if self.cipher_mode == AES.MODE_EAX:
                cipher = AES.new(key=self.key, mode=self.cipher_mode, nonce=self.nonce)
                cipherbytes, tag = cipher.encrypt_and_digest(data)
                return AES_Encrypt.EncryptRetClass(
                    cipher_mode    = self.cipher_mode_str,
                    ciphertext_b64 = b64encode(cipherbytes).decode(self.text_encoding),
                    plaintext_b64  = None,
                    tag_b64        = b64encode(tag).decode(self.text_encoding),
                    nonce_b64      = b64encode(self.nonce).decode(self.text_encoding)
                )
            elif self.cipher_mode == AES.MODE_CBC:
                # 1-16, make sure not 0, other wise last byte will not be block length
                length = AES_Encrypt.DEFAULT_BLOCK_SIZE_AES_CBC - (len(data) % AES_Encrypt.DEFAULT_BLOCK_SIZE_AES_CBC)
                # Pad data with the original length, so when we decrypt we can just take data[-1]
                # as length of data block
                data += bytes(chr(length), encoding=STR_ENCODING) * length
                Log.debugdebug(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Padded length = ' + str(length)
                )
                cipher = AES.new(key=self.key, mode=self.cipher_mode, iv=self.nonce)
                cipherbytes = cipher.encrypt(data)
                return AES_Encrypt.EncryptRetClass(
                    cipher_mode    = self.cipher_mode_str,
                    ciphertext_b64 = b64encode(cipherbytes).decode(self.text_encoding),
                    plaintext_b64  = None,
                    tag_b64        = None,
                    nonce_b64      = b64encode(self.nonce).decode(self.text_encoding)
                )
            else:
                raise Exception(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Unsupported mode "' + str(self.cipher_mode) + '".'
                )
        except Exception as ex:
            errmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': Error encoding data "' + str(data) + '" using AES ". Exception: ' + str(ex)
            Log.error(errmsg)
            raise Exception(errmsg)

    def decode(
            self,
            ciphertext
    ):
        try:
            if self.cipher_mode == AES.MODE_EAX:
                cipher = AES.new(key=self.key, mode=self.cipher_mode, nonce=self.nonce)
                cipherbytes = b64decode(ciphertext.encode(self.text_encoding))
                data = cipher.decrypt(cipherbytes)
            elif self.cipher_mode == AES.MODE_CBC:
                cipher = AES.new(key=self.key, mode=self.cipher_mode, iv=self.nonce)
                cipherbytes = b64decode(ciphertext.encode(self.text_encoding))
                data = cipher.decrypt(cipherbytes)
                Log.debugdebug(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Decrypted data length = ' + str(len(data)) + ', modulo 16 = ' + str(len(data) % 128/8)
                )
                # Remove last x bytes encoded in the padded bytes
                data = data[:-data[-1]]
            else:
                raise Exception(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Unsupported mode "' + str(self.cipher_mode) + '".'
                )

            return str(data, encoding=STR_ENCODING)
        except Exception as ex:
            errmsg = str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': Error decoding data "' + str(ciphertext) + '" using AES ". Exception: ' + str(ex)
            Log.error(errmsg)
            raise Exception(errmsg)


class EncryptUnitTest:
    def __init__(self, ut_params):
        return

    def run_unit_test(self):
        res_final = ut.ResultObj(count_ok=0, count_fail=0)

        long_str = ''
        for i in range(10000):
            long_str += random.choice(AES_Encrypt.CHARS_STR)
        sentences = [
            '니는 먹고 싶어',
            'Дворянское ГНЕЗДО',
            '没问题 大陆 经济',
            '存款方式***2019-12-11 11：38：46***',
            '1234567890123456',
            long_str
        ]

        key = b'Sixteen byte key'
        nonce = b'0123456789xxyyzz'

        for mode in [AES_Encrypt.AES_MODE_CBC, AES_Encrypt.AES_MODE_EAX]:
            # aes_obj = AES_Encrypt(key=AES_Encrypt.generate_random_bytes(size=32, printable=True))
            aes_obj = AES_Encrypt(
                key   = key + key,
                mode  = mode,
                nonce = nonce
            )
            for s in sentences:
                Log.debug('Encrypting "' + str(s) + '"')
                data_bytes = bytes(s.encode(encoding=STR_ENCODING))
                Log.debug('Data length in bytes = ' + str(len(data_bytes)))
                res = aes_obj.encode(
                    data=data_bytes
                )
                ciphertext = res.ciphertext_b64
                Log.debug('Encrypted as "' + str(ciphertext) + '"')

                plaintext = aes_obj.decode(ciphertext=ciphertext)
                Log.debug('Decrypted as "' + plaintext + '"')

                res_final.update_bool(res_bool=ut.UnitTest.assert_true(
                    observed = plaintext,
                    expected = s,
                    test_comment = 'mode "' + str(mode) + '" s=' + str(s)
                                   + '" encrypted to "' + str(ciphertext)
                                   + '", decrypted back to "' + str(plaintext)
                ))

        return res_final


if __name__ == '__main__':
    Log.LOGLEVEL = Log.LOG_LEVEL_DEBUG_2

    res = EncryptUnitTest(ut_params=None).run_unit_test()

    key_str = 'Sixteen byte key'
    s = '0077788'
    ciphertext_b64 = '2zNslaKcIy9iqeVo8i5whQ=='
    nonce_b64 = 'PNCt4LieRuC4v+OFnF\/tkw=='

    aes_test = AES_Encrypt(
        key   = key_str.encode('utf-8'),
        mode  = AES_Encrypt.AES_MODE_CBC,
        nonce = b64decode(nonce_b64.encode(encoding='utf-8'))
    )

    plaintext = aes_test.decode(
        ciphertext = ciphertext_b64
    )
    print(plaintext)
