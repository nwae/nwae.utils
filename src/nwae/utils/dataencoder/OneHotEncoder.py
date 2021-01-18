# -*- coding: utf-8 -*-

import numpy as np
from nwae.utils.Log import Log
from inspect import currentframe, getframeinfo
import nwae.utils.UnitTest as ut


class OneHotEncoder:

    def __init__(
            self
    ):
        self.unique_feature_dict = {}
        return

    def create_unique_dictionary(
            self,
            feature_list
    ):
        # Getting all the unique tokens
        feature_list_unique = list(set(feature_list))
        # After taking set(), the order becomes unpredictable already, so we might as well sort it
        feature_list_unique.sort()

        # Creating the dictionary for the unique words
        self.unique_feature_dict = {}
        for i, tok in enumerate(feature_list_unique):
            self.unique_feature_dict.update({
                tok: i
            })
        return self.unique_feature_dict

    def get_unique_feature_dict(self):
        return self.unique_feature_dict

    def encode(
            self,
            feature_list,
            unique_feature_dict = None
    ):
        if unique_feature_dict is None:
            unique_feature_dict = self.create_unique_dictionary(
                feature_list = feature_list
            )

        # Defining the number of features
        n_features = len(unique_feature_dict)

        # Getting all the unique features
        features = list(unique_feature_dict.keys())

        # Creating the X and Y matrices using one hot encoding
        X = []

        for i, f in enumerate(features):
            # Getting the indices
            feature_index = unique_feature_dict.get(f)

            # Creating the placeholders
            X_row = np.zeros(n_features)

            # One hot encoding the main word
            X_row[feature_index] = 1

            # Appending to the main matrices
            X.append(X_row)

        # Converting the matrices into an array
        return np.asarray(X)


class OneHotEncoderUnitTest:
    def __init__(self):
        return

    def run_unit_test(self):
        res_final = ut.ResultObj(count_ok=0, count_fail=0)

        token_list = [
            'аккаунт', 'популярный', 'южнокорея', 'чат-бот', 'заблокировать', 'жалоба', 'ненависть', 'высказывание',
            'адрес', 'сексуальный', 'меньшинство', 'передать', 'газета', 'диалог', 'пользователь', 'бот', 'имя',
            'lee', 'ludа', 'назвать', 'лесбиянка', 'жуткий', 'признать', 'ненавидеть', 'слово', 'издание', 'первый',
            'случай', 'искусственный', 'интеллект', 'сталкиваться', 'обвинение', 'нетерпимость', 'дискриминация',
        ]
        enc = OneHotEncoder()
        x_oh = enc.encode(
            feature_list=token_list
        )
        unique_word_dict = enc.get_unique_feature_dict()
        l = len(x_oh[0])
        v = np.array(list(range(l)))
        for i, t in enumerate(enc.get_unique_feature_dict().keys()):
            # Make sure the '1' is in the correct position
            res_final.update_bool(res_bool=ut.UnitTest.assert_true(
                observed = np.sum(v * x_oh[i]) == unique_word_dict[t],
                expected = True,
                test_comment = 'token "' + str(t) + '" #' + str(np.sum(v * x_oh[i]))
                               + '==' + str(unique_word_dict[t]) + ': ' + str(x_oh[i])
            ))

        return res_final


if __name__ == '__main__':
    # Log.LOGLEVEL = Log.LOG_LEVEL_DEBUG_1
    OneHotEncoderUnitTest().run_unit_test()
    exit(0)
