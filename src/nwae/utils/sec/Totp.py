# -*- coding: utf-8 -*-

import nwae.utils.Log as lg
import pyotp
import nwae.utils.Encode as en64
# pip install qrcode
import qrcode
# pip install Pillow
from PIL import Image


class Totp:

    def __init__(
            self
    ):
        return

    @staticmethod
    def generate_base32_secret_key():
        # returns a 16 character base32 secret. Compatible with Google Authenticator and other OTP apps
        return pyotp.random_base32()

    @staticmethod
    def generate_provisioning_uri(
            base32secret,
            user_id_or_email,
            issuer_name
    ):
        try:
            val = pyotp.totp.TOTP(base32secret).provisioning_uri(
                user_id_or_email,
                issuer_name = issuer_name
            )
            return val
        except Exception as ex:
            errmsg = 'Error generating provisioning URI, (hash of) shared secret "'\
                     + str(en64.Encode.encode_base64(base32secret))\
                     + '" for user id/email "' + str(user_id_or_email) \
                     + '", issuer "' + str(issuer_name) + '". Got exception: ' + str(ex) + '.'
            lg.Log.error(errmsg)
            raise Exception(errmsg)

    @staticmethod
    def generate_image_for_provisioning_uri(
            provisioning_uri,
            img_filename
    ):
        try:
            qr_obj = qrcode.make(
                data=provisioning_uri
            )
            fh = open(img_filename, 'wb')
            qr_obj.save(stream=fh)
            qr_img = Image.open(img_filename)
            return qr_img
        except Exception as ex:
            errmsg = 'Error making QR or saving image to file "' + str(img_filename)\
                     + '". Got exception: ' + str(ex) + '.'
            lg.Log.error(errmsg)
            raise Exception(errmsg)

    def verify_totp(
            self,
            totp_base32_secret,
            otp
    ):
        try:
            totp = pyotp.TOTP(totp_base32_secret)
            res = totp.verify(
                otp = otp
            )
            return res
        except Exception as ex:
            errmsg = 'Error verifying TOTP, (hash of) shared secret "'\
                     + str(en64.Encode.encode_base64(totp_base32_secret))\
                     + '" for OTP "' + str(otp) + '". Got exception: ' + str(ex) + '.'
            lg.Log.error(errmsg)
            raise Exception(errmsg)


if __name__ == '__main__':
    #
    # Example usage
    #
    # First both parties must have a shared secret already
    b32secret = Totp.generate_base32_secret_key()
    print('Secret "' + str(b32secret) + '".')
    # This is to generate QR Code for user to scan from phone, etc.
    puri = Totp.generate_provisioning_uri(
        base32secret = b32secret,
        user_id_or_email = 'alice@nwae.com',
        issuer_name = 'Nwae Secure App'
    )
    print('Provisioning URI "' + str(puri) + '"')
    qr_img = Totp.generate_image_for_provisioning_uri(
        provisioning_uri = puri,
        img_filename = '/tmp/qr.jpg'
    )
    # Show the image for user to scan
    qr_img.show()

    # Client side will generate a totp
    totp_client = pyotp.TOTP(b32secret)
    otp = totp_client.now()
    print('OTP "' + str(otp) + '"')

    # Server side will verify
    totp_server = Totp()
    verify_otp = totp_server.verify_totp(
        totp_base32_secret = b32secret,
        otp = otp
    )
    print('Verify = ' + str(verify_otp))

    exit(0)
