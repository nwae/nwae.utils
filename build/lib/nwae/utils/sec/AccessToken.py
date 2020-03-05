# -*- coding: utf-8 -*-

import string
import random
from nwae.utils.Hash import Hash
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from datetime import datetime, timedelta


def generate_random_string(
        n,
        # The list of characters to randomize from
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + '_@'
):
    return ''.join(random.choices(chars, k=n))


#
# Shared Secret, with Challenge
#
class AccessTokenSharedsecretChallenge:
    
    def __init__(
            self,
            shared_secret,
            # We compare this to our own calculation to verify if the same or not
            test_challenge,
            # Random string sent to client as challenge
            challenge = None,
            algo_hash = Hash.ALGO_SHA256
    ):
        self.shared_secret = shared_secret
        self.challenge = challenge
        self.test_challenge = test_challenge
        self.algo_hash = algo_hash
        return

    @staticmethod
    def create_test_challenge_string(
            shared_secret,
            challenge_string,
            algo_hash = Hash.ALGO_SHA256
    ):
        test_challenge = Hash.hash(
            string = challenge_string + shared_secret,
            algo   = algo_hash
        )
        return test_challenge

    # For client to create
    @staticmethod
    def create_totp_style_challenge_response(
            shared_secret,
            datetime_val = None,
            algo_hash = Hash.ALGO_SHA256
    ):
        if datetime_val is None:
            datetime_val = datetime.now()
        test_challenge = AccessTokenSharedsecretChallenge.create_test_challenge_string(
            shared_secret    = shared_secret,
            challenge_string = datetime_val.strftime('%Y-%m-%d %H:%M:%S'),
            algo_hash        = algo_hash
        )
        return test_challenge

    # For client to create
    @staticmethod
    def create_totp_otp(
            shared_secret
    ):
        import pyotp
        s = str(shared_secret)
        # Pad to 8 modulo with last character in shared secret
        shared_secret_pad = s + s[-1] * ((8 - len(s) % 8) % 8)
        totp_client = pyotp.TOTP(shared_secret_pad)
        otp = totp_client.now()
        return otp

    def verify_totp_otp(
            self,
            valid_window = 1
    ):
        try:
            import pyotp
            s = str(self.shared_secret)
            # Pad to 8 modulo with last character in shared secret
            shared_secret_pad = s + s[-1] * ((8 - len(s) % 8) % 8)
            totp_obj = pyotp.TOTP(shared_secret_pad)
            res =  totp_obj.verify(
                otp = self.test_challenge,
                valid_window = valid_window
            )
            # print('Secret=' + str(self.shared_secret) + ', otp=' + str(self.test_challenge) + ' ' + str(res))
            return res
        except Exception as ex:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error TOTP authentication, exception: ' + str(ex)
            )
            return False

    #
    # No challenge, just receive authentication info from client in TOTP style
    # Client hashes/encrypts <timestamp> + <shared_secret>
    #
    def verify_totp_style(
            self,
            # We test for <tolerance_secs> back
            tolerance_secs = 30
    ):
        now = datetime.now()
        try:
            for i in range(tolerance_secs):
                t_test = now - timedelta(seconds=i)
                Log.debugdebug(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Trying ' + str(t_test.strftime('%Y-%m-%d %H:%M:%S'))
                )
                test_challenge_calc = AccessTokenSharedsecretChallenge.create_totp_style_challenge_response(
                    shared_secret = self.shared_secret,
                    datetime_val  = t_test,
                    algo_hash     = self.algo_hash
                )
                res = self.__compare_test_challenge(
                    test_challenge_calc = test_challenge_calc
                )
                if res == True:
                    return res
            return False
        except Exception as ex:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Exception for shared secret "' + str(self.shared_secret)
                + '", totp style test challenge "' + str(self.test_challenge) + '": ' + str(ex)
            )
            return False

    #
    # Challenge Response Verification
    #
    def verify(self):
        try:
            test_challenge_calc = AccessTokenSharedsecretChallenge.create_test_challenge_string(
                shared_secret    = self.shared_secret,
                challenge_string = self.challenge,
                algo_hash        = self.algo_hash
            )
            return self.__compare_test_challenge(
                test_challenge_calc = test_challenge_calc
            )
        except Exception as ex:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Exception for shared secret "' + str(self.shared_secret)
                + '", challenge "' + str(self.challenge) + '": ' + str(ex)
            )
            return False

    def __compare_test_challenge(
            self,
            test_challenge_calc
    ):
        if test_challenge_calc != self.test_challenge:
            Log.debugdebug(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Test Challenge Fail. Challenge string "' + str(self.challenge)
                + '". Test Challenge Calculated "' + str(test_challenge_calc)
                + '", test challenge given "' + str(self.test_challenge)
            )
            return False
        return True

if __name__ == '__main__':
    Log.LOGLEVEL = Log.LOG_LEVEL_DEBUG_1
    Log.DEBUG_PRINT_ALL_TO_SCREEN = True

    shared_secret = generate_random_string(n=100)
    challenge = generate_random_string(n=1000)
    test_challenge = Hash.hash(string=challenge + shared_secret, algo=Hash.ALGO_SHA256)
    print('Shared Secret: ' + str(shared_secret))
    print('Challenge: ' + str(challenge))

    obj = AccessTokenSharedsecretChallenge(
        shared_secret  = shared_secret,
        challenge      = challenge,
        test_challenge = test_challenge
    )
    print('Verify (expect True): ' + str(obj.verify()))

    obj.test_challenge = 'asdfasd'
    print('Verify (expect False): ' + str(obj.verify()))

    #
    # Verify TOTP style
    #
    obj.test_challenge = AccessTokenSharedsecretChallenge.create_totp_style_challenge_response(
        shared_secret = shared_secret,
        datetime_val = datetime.now() - timedelta(seconds=20)
    )
    print('Client test challenge=' + str(obj.test_challenge))
    print('Verify (expect True): ' + str(obj.verify_totp_style()))

    obj.test_challenge = AccessTokenSharedsecretChallenge.create_totp_style_challenge_response(
        shared_secret = shared_secret,
        datetime_val = datetime.now() - timedelta(seconds=35)
    )
    print('Client test challenge=' + str(obj.test_challenge))
    print('Verify (expect False): ' + str(obj.verify_totp_style()))

    #
    # Verify TOTP
    #
    import pyotp
    shared_secret_base32 = 'asdfjkleasd'
    obj.shared_secret = shared_secret_base32
    print('Random base 32 secret = ' + str(shared_secret_base32))
    obj.test_challenge = AccessTokenSharedsecretChallenge.create_totp_otp(
        shared_secret = shared_secret_base32
    )
    print('Client OTP=' + str(obj.test_challenge))
    print('Verify (expect True): ' + str(obj.verify_totp_otp()))

    obj.test_challenge = AccessTokenSharedsecretChallenge.create_totp_otp(
        shared_secret = shared_secret_base32
    )
    obj.test_challenge = 293847
    print('Client test challenge=' + str(obj.test_challenge))
    print('Verify (expect False): ' + str(obj.verify_totp_otp()))

    exit(0)
