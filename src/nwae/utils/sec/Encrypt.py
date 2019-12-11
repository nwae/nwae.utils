# -*- coding: utf-8 -*-

import os
import random
# pycryptodome
from Crypto.Cipher import AES
from nwae.utils.Log import Log


STR_ENCODING = 'utf-8'


class AES_Encrypt:

    SIZE_NONCE = 16

    @staticmethod
    def generate_random_bytes(size = 16, printable = False):
        if not printable:
            return os.urandom(size)
        else:
            s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'\
                +'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфцчшщъыьэюя'\
                + 'ㅂㅈㄷㄱ쇼ㅕㅑㅐㅔㅁㄴㅇㄹ호ㅓㅏㅣㅋㅌㅊ퓨ㅜㅡㅃㅉㄸㄲ쑈ㅕㅑㅒㅖㅁㄴㅇㄹ호ㅓㅏㅣㅋㅌㅊ퓨ㅜㅡ'\
                + 'ๅ/_ภถุึคตจขชๆไำพะัีรนยฟหกดเ้่าสผปแอิืท+๑๒๓๔ู฿๕๖๗๘๙๐ฎฑธ'\
                + '1234567890' \
                + '`~!@#$%^&*()_+-=[]\{}|[]\\;\':",./<>?'
            rs = ''.join(random.choice(s) for i in range(size))
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
            data
    ):
        try:
            cipher = AES.new(key=self.key, mode=self.cipher_mode, nonce=self.nonce)
            ciphertext, tag = cipher.encrypt_and_digest(data)
            return (ciphertext, tag)
        except Exception as ex:
            errmsg = 'Error encoding data "' + str(data) + '" using AES ". Exception: ' + str(ex)
            Log.error(errmsg)
            return None

    def decode(
            self,
            ciphertext
    ):
        try:
            cipher = AES.new(key=self.key, mode=self.cipher_mode, nonce=self.nonce)
            data = cipher.decrypt(ciphertext)
            return str(data, encoding=STR_ENCODING)
        except Exception as ex:
            errmsg = 'Error decoding data "' + str(ciphertext) + '" using AES ". Exception: ' + str(ex)
            Log.error(errmsg)
            return None


if __name__ == '__main__':
    Log.LOGLEVEL = Log.LOG_LEVEL_INFO
    sentences = [
        '니는 먹고 싶어',
        'Дворянское ГНЕЗДО',
        '没问题 大陆 经济'
    ]

    aes_obj = AES_Encrypt(key=AES_Encrypt.generate_random_bytes(size=32, printable=True))
    for s in sentences:
        print('Encrypting "' + str(s) + '"')
        (ciphertext, tag) = aes_obj.encode(
            data=bytes(s.encode(encoding=STR_ENCODING))
        )
        print('Encrypted as "' + str(ciphertext) + '"')
        plaintext = aes_obj.decode(ciphertext = ciphertext)
        print('Decrypted as "' + plaintext + '"')

        if s == plaintext:
            print('PASS')
        else:
            print('FAIL')
