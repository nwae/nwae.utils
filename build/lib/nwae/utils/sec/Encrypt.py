# -*- coding: utf-8 -*-

import os
import random
# pycryptodome
from Crypto.Cipher import AES
from nwae.utils.Log import Log


STR_ENCODING = 'utf-8'


class AES_Encrypt:

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
            mode = AES.MODE_EAX
    ):
        self.key = key
        Log.debug('Using key ' + str(str(self.key)) + '. Size = ' + str(len(self.key)) + '.')
        self.cipher_mode = mode
        if nonce is None:
            nonce = AES_Encrypt.generate_random_bytes(size=AES_Encrypt.SIZE_NONCE, printable=True)

        self.nonce = nonce
        Log.debug('Using nonce "' + str(self.nonce) + '". Size = ' + str(len(self.nonce)))
        return

    def encode(
            self,
            # bytes format
            data
    ):
        try:
            if self.cipher_mode == AES.MODE_EAX:
                cipher = AES.new(key=self.key, mode=self.cipher_mode, nonce=self.nonce)
                ciphertext, tag = cipher.encrypt_and_digest(data)
            elif self.cipher_mode == AES.MODE_CBC:
                # 1-16, make sure not 0, other wise last byte will not be block length
                length = AES_Encrypt.DEFAULT_BLOCK_SIZE_AES_CBC - (len(data) % AES_Encrypt.DEFAULT_BLOCK_SIZE_AES_CBC)
                # Pad data with the original length, so when we decrypt we can just take data[-1]
                # as length of data block
                data += bytes(chr(length), encoding=STR_ENCODING) * length
                Log.debug('Padded length = ' + str(length))
                cipher = AES.new(key=self.key, mode=self.cipher_mode, iv=self.nonce)
                ciphertext = cipher.encrypt(data)
            else:
                raise Exception('Unsupported mode "' + str(self.cipher_mode) + '".')

            return ciphertext
        except Exception as ex:
            errmsg = 'Error encoding data "' + str(data) + '" using AES ". Exception: ' + str(ex)
            Log.error(errmsg)
            return None

    def decode(
            self,
            ciphertext
    ):
        try:
            if self.cipher_mode == AES.MODE_EAX:
                cipher = AES.new(key=self.key, mode=self.cipher_mode, nonce=self.nonce)
                data = cipher.decrypt(ciphertext)
            elif self.cipher_mode == AES.MODE_CBC:
                cipher = AES.new(key=self.key, mode=self.cipher_mode, iv=self.nonce)
                data = cipher.decrypt(ciphertext)
                Log.debug('Decrypted data length = ' + str(len(data)) + ', modulo 16 = ' + str(len(data) % 128/8))
                # Remove last x bytes encoded in the padded bytes
                data = data[:-data[-1]]
            else:
                raise Exception('Unsupported mode "' + str(self.cipher_mode) + '".')

            return str(data, encoding=STR_ENCODING)
        except Exception as ex:
            errmsg = 'Error decoding data "' + str(ciphertext) + '" using AES ". Exception: ' + str(ex)
            Log.error(errmsg)
            return None


if __name__ == '__main__':
    Log.LOGLEVEL = Log.LOG_LEVEL_DEBUG_1
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
    # aes_obj = AES_Encrypt(key=AES_Encrypt.generate_random_bytes(size=32, printable=True))
    aes_obj = AES_Encrypt(
        key   = key+key,
        mode  = AES.MODE_CBC,
        nonce = nonce
    )
    for s in sentences:
        print('Encrypting "' + str(s) + '"')
        data_bytes = bytes(s.encode(encoding=STR_ENCODING))
        print('Data length in bytes = ' + str(len(data_bytes)))
        ciphertext = aes_obj.encode(
            data = data_bytes
        )
        print('Encrypted as "' + str(ciphertext) + '"')
        plaintext = aes_obj.decode(ciphertext = ciphertext)
        print('Decrypted as "' + plaintext + '"')

        if s == plaintext:
            print('PASS')
        else:
            raise Exception('FAIL')
