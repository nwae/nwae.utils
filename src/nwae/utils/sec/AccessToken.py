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
                td = timedelta(seconds=i)
                t_test = now - td
                s = t_test.strftime('%Y-%m-%d %H:%M:%S')
                Log.debugdebug(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Trying ' + str(s)
                )
                test_challenge_calc = Hash.hash(
                    string = s + shared_secret,
                    algo   = self.algo_hash
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
            test_challenge_calc = Hash.hash(
                string = self.challenge + self.shared_secret,
                algo   = self.algo_hash
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
    print('Verify: ' + str(obj.verify()))

    obj.test_challenge = 'asdfasd'
    print('Verify: ' + str(obj.verify()))

    #
    # Verify TOTP style
    #
    now = datetime.now() - timedelta(seconds=5)
    s = now.strftime('%Y-%m-%d %H:%M:%S')
    test_challenge = Hash.hash(string=s + shared_secret, algo=Hash.ALGO_SHA256)

    print('s=' + str(s) + ', test challenge=' + str(test_challenge))
    obj.test_challenge = test_challenge
    print('Verify: ' + str(obj.verify_totp_style()))

    exit(0)
