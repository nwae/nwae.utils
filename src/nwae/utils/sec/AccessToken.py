# -*- coding: utf-8 -*-

import string
import random
from nwae.utils.Hash import Hash
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe


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
            # Random string sent to client as challenge
            challenge,
            # We compare this to our own calculation to verify if the same or not
            test_challenge,
            algo_hash = Hash.ALGO_SHA256
    ):
        self.shared_secret = shared_secret
        self.challenge = challenge
        self.test_challenge = test_challenge
        self.algo_hash = algo_hash
        return

    def verify(self):
        test_challenge_calc = Hash.hash(
            string = self.challenge + self.shared_secret,
            algo   = self.algo_hash
        )
        if test_challenge_calc != self.test_challenge:
            Log.debug(
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

    exit(0)
