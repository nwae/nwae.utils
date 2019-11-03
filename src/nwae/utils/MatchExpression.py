# -*- coding: utf-8 -*-

import nwae.utils.Log as lg
from inspect import getframeinfo, currentframe
import re
import nwae.utils.StringUtils as su


#
# A Layer of Abstraction above Regular Expressions
#
# Human Level Description of extracting parameters from sentence
# WITHOUT technical regular expression syntax.
#
# Higher Level Abstraction to re.match() to extract parameters
# Never allow user to specify their own regex, this is the idea of this
# abstraction or simplification - always keep it simple, support a new
# var type if need.
#
# Language
#   var_1;var_2;var_3;..
# where
#   var_x = <var_name>,<var_type>,<expression_1>&<expression_2>&...
#
# In human level, the above says, "Please extract variable x using <var_name>
# (e.g. email, date, and this variable is of type <var_type> (e.g. float, email,
# time") and expect a person to type words "<expression_1>" or "<expression_2>"...
# when presenting this parameter"
#
# <var_name> can be anything but must be unique among the variables
# <var_type> can be
#    - int
#    - float
#    - number (string instead of integer and will not remove leading 0's)
#    - time (12:30:55, 23:59)
#    - datetime (20190322 23:59:11, 2019-03-22 23:59, 2019-03-22)
#    - email
# <expression_x> is the word you expect to see before/after the parameter
#
class MatchExpression:

    MEX_OBJECT_VARS_TYPE = 'type'
    MEX_OBJECT_VARS_EXPRESIONS = 'expressions'

    # Separates the different variables definition. e.g. 'm,float,mass&m;c,float,light&speed'
    MEX_VAR_DEFINITION_SEPARATOR = ';'
    # Separates the description of the same variable. e.g. 'm,float,mass&m'
    MEX_VAR_DESCRIPTION_SEPARATOR = ','
    # Separates the names of a variable. e.g. 'mass&m'
    MEX_VAR_EXPRESSIONS_SEPARATOR = '&'

    MEX_TYPE_FLOAT  = 'float'
    MEX_TYPE_INT    = 'int'
    # String format and will not remove leading 0's
    MEX_TYPE_NUMBER = 'number'
    # e.g. 10:12:36, 12:15
    MEX_TYPE_TIME   = 'time'

    MEX_TYPE_DATETIME = 'datetime'
    # e.g. me@gmail.com
    MEX_TYPE_EMAIL  = 'email'

    #
    # Regex Constants
    #
    USERNAME_CHARS = 'a-zA-Z0-9_.-'
    # These characters need to be bracketed if found in mex expressions
    COMMON_REGEX_CHARS = ('*', '+', '[', ']', '{', '}', '|')

    TERM_LEFT = 'front'
    TERM_RIGHT  = 'back'
    #
    # Mapping of regular expressions to data type, you may pass in your custom one at constructor
    #
    MAP_VARTYPE_REGEX = {
        MEX_TYPE_FLOAT: {
            TERM_LEFT: [
                # In front of variable expression
                '.*[^0-9\-]+([+\-]*[0-9]+[.][0-9]*)',
                # In front of variable expression at the start of sentence
                '^([+\-]*[0-9]+[.][0-9]*)'
            ],
            TERM_RIGHT: [
                # After or at the back of variable expression
                '([+\-]*[0-9]+[.][0-9]*).*'
            ]
        },
        MEX_TYPE_INT: {
            TERM_LEFT: [
                # In front of variable expression
                '.*[^0-9\-]+([+\-]*[0-9]+)',
                # In front of variable expression at the start of sentence
                '^([+\-]*[0-9]+)'
            ],
            TERM_RIGHT: [
                # After or at the back of variable expression
                '([+\-]*[0-9]+).*'
            ]
        },
        MEX_TYPE_NUMBER: {
            TERM_LEFT: [
                # In front of variable expression
                '.*[^0-9\-]+([+\-]*[0-9]+)',
                # In front of variable expression at the start of sentence
                '^([+\-]*[0-9]+)'
            ],
            TERM_RIGHT: [
                # After or at the back of variable expression
                '([+\-]*[0-9]+).*'
            ]
        },
        MEX_TYPE_TIME: {
            TERM_LEFT: [
                # HHMMSS. Check this first
                # HHMMSS. In front of variable expression
                '.*[^0-9]+([0-9]+[:][0-9]+[:][0-9]+)',
                # HHMMSS. In front of variable expression at the start of sentence
                '^([0-9]+[:][0-9]+[:][0-9]+)',
                # HHMM. Check this only after checking HHMMSS
                # HHMM. In front of variable expression
                '.*[^0-9]+([0-9]+[:][0-9]+)',
                # HHMM. In front of variable expression at the start of sentence
                '^([0-9]+[:][0-9]+)',
            ],
            TERM_RIGHT: [
                # HHMMSS. After or at the back of variable expression
                '([0-9]+[:][0-9]+[:][0-9]+).*',
                # HHMM. After or at the back of variable expression
                '([0-9]+[:][0-9]+).*'
            ]
        },
        MEX_TYPE_DATETIME: {
            TERM_LEFT: [
                # "yyyymmdd HHMMSS". Check this first
                # HHMMSS. In front of variable expression
                '.*[^0-9]+([0-9]{4}[-]*[0-1][0-9][-*][0-3][0-9][ ]+[0-9]+[:][0-9]+[:][0-9]+)',
                # "yyyymmdd HHMMSS". In front of variable expression at the start of sentence
                '^([0-9]{4}[-]*[0-1][0-9][-]*[0-3][0-9][ ]+[0-9]+[:][0-9]+[:][0-9]+)',
                # "yyyymmdd HHMM". Check this only after checking "yyyymmdd HHMMSS"
                # "yyyymmdd HHMM". In front of variable expression
                '.*[^0-9]+([0-9]{4}[-]*[0-1][0-9][-]*[0-3][0-9][ ]+[0-9]+[:][0-9]+)',
                # "yyyymmdd HHMM". In front of variable expression at the start of sentence
                '^([0-9]{4}[-]*[0-1][0-9][-]*[0-3][0-9][ ]+[0-9]+[:][0-9]+)',
                # "yyyymmdd". In front of variable expression
                '.*[^0-9]+([0-9]{4}[-]*[0-1][0-9][-]*[0-3][0-9])',
                # "yyyymmdd". In front of variable expression at the start of sentence
                '^([0-9]{4}[-]*[0-1][0-9][-]*[0-3][0-9])',
            ],
            TERM_RIGHT: [
                # "yyyymmdd HHMMSS". After or at the back of variable expression
                '([0-9]{4}[-]*[0-1][0-9][-*][0-3][0-9][ ]+[0-9]+[:][0-9]+[:][0-9]+).*',
                # "yyyymmdd HHMM". After or at the back of variable expression
                '([0-9]{4}[-]*[0-1][0-9][-*][0-3][0-9][ ]+[0-9]+[:][0-9]+).*',
                # "yyyymmdd"". After or at the back of variable expression
                '([0-9]{4}[-]*[0-1][0-9][-*][0-3][0-9]).*',
            ]
        },
        MEX_TYPE_EMAIL: {
            TERM_LEFT: [
                # In front of variable expression
                '.*[^' + USERNAME_CHARS + ']+' + '([' + USERNAME_CHARS + ']+' + '[@][a-zA-Z0-9]+[.][a-zA-Z]+)',
                # In front of variable expression at the start of sentence
                '^([' + USERNAME_CHARS + ']+' + '[@][a-zA-Z0-9]+[.][a-zA-Z]+)'
            ],
            TERM_RIGHT: [
                # After or at the back of variable expression
                # Note that if given math expressions are nothing or '', then
                # 'email@x.com' will be returned correctly on the left side but
                # the right side will return 'l@x.com'.
                # The user needs to choose the right one
                '([' + USERNAME_CHARS + ']+' + '[@][a-zA-Z0-9]+[.][a-zA-Z]+).*'
            ]
        }
    }

    def __init__(
            self,
            pattern,
            sentence,
            map_vartype_to_regex = MAP_VARTYPE_REGEX,
            case_sensitive = False
    ):
        self.pattern = pattern
        self.sentence = sentence
        self.case_sensitive = case_sensitive
        if not self.case_sensitive:
            self.sentence = str(self.sentence).lower()
        self.map_vartype_to_regex = map_vartype_to_regex
        lg.Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Pattern "' + str(self.pattern)
            + '" sentence "' + str(self.sentence) + '".'
        )
        #
        # Decode the model variables
        #
        self.mex_obj_vars = self.decode_match_expression_pattern()
        lg.Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Model Object vars: ' + str(self.mex_obj_vars)
        )
        return

    #
    # Extract from string encoding 'm,float,mass&m;c,float,light&speed' into something like:
    #   {
    #      'm': {
    #         'type': 'float',
    #         'names': ['mass', 'm']
    #      },
    #      'c': {
    #         'type': 'float',
    #         'names': ['speed', 'light']
    #      }
    #   }
    #
    def decode_match_expression_pattern(
            self
    ):
        try:
            var_encoding = {}

            # Use our own split function that will ignore escaped built-in separator
            # Here we split "m,float,mass&m;c,float,light&speed" into ['m,float,mass&m', 'c,float,light&speed']
            str_encoding = su.StringUtils.split(
                string = self.pattern,
                split_word = MatchExpression.MEX_VAR_DEFINITION_SEPARATOR
            )
            for unit_mex_pattern in str_encoding:
                unit_mex_pattern = su.StringUtils.trim(unit_mex_pattern)
                if unit_mex_pattern == '':
                    continue
                # Use our own split function that will ignore escaped built-in separator
                # Here we split 'm,float,mass&m' into ['m','float','mass&m']
                var_desc = su.StringUtils.split(
                    string = unit_mex_pattern,
                    split_word = MatchExpression.MEX_VAR_DESCRIPTION_SEPARATOR
                )

                if len(var_desc) < 3:
                    raise Exception(
                        'Mex pattern must have at least 3 parts, got only ' + str(len(unit_mex_pattern))
                        + ' for unit mex pattern "' + str(unit_mex_pattern)
                        + '" from mex pattern "' + str(self.pattern)
                    )

                part_var_id = su.StringUtils.trim(var_desc[0])
                part_var_type = su.StringUtils.trim(var_desc[1])
                part_var_expressions = su.StringUtils.trim(var_desc[2])

                expressions_arr = su.StringUtils.split(
                        string = part_var_expressions,
                        split_word = MatchExpression.MEX_VAR_EXPRESSIONS_SEPARATOR
                    )
                corrected_expressions_arr = []
                # Bracket characters that are common regex key characters,
                # as they are inserted into regex later on
                for expression in expressions_arr:
                    expression = su.StringUtils.trim(expression)
                    corrected_expression = ''
                    for i in range(len(expression)):
                        if expression[i] in MatchExpression.COMMON_REGEX_CHARS:
                            corrected_expression = corrected_expression + '[' + expression[i] + ']'
                        else:
                            corrected_expression = corrected_expression + expression[i]
                    corrected_expressions_arr.append(corrected_expression)

                var_encoding[part_var_id] = {
                    # Extract 'float' from ['m','float','mass&m']
                    MatchExpression.MEX_OBJECT_VARS_TYPE: part_var_type,
                    # Extract ['mass','m'] from 'mass&m'
                    MatchExpression.MEX_OBJECT_VARS_EXPRESIONS: corrected_expressions_arr
                }
                lg.Log.info(
                    str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': Successfully decoded vars object item "'
                    + str(part_var_id) + '": ' + str(var_encoding[var_desc[0]])
                )
            return var_encoding
        except Exception as ex:
            errmsg = str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Failed to get var encoding for mex pattern "'\
                     + str(self.pattern) + '". Exception ' + str(ex) + '.'
            lg.Log.error(errmsg)
            raise Exception(errmsg)

    #
    # Extract variables from string
    #
    def extract_variable_values(
            self
    ):
        lg.Log.debug(
            str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Extracting vars from "' + str(self.sentence) + '", using mex encoding ' + str(self.mex_obj_vars)
        )

        var_values = {}

        # Look one by one
        for var in self.mex_obj_vars.keys():
            # Left and right values
            var_values[var] = (None, None)
            # Get the names and join them using '|' for matching regex
            var_expressions = '|'.join(self.mex_obj_vars[var][MatchExpression.MEX_OBJECT_VARS_EXPRESIONS])
            data_type = self.mex_obj_vars[var][MatchExpression.MEX_OBJECT_VARS_TYPE]

            #
            # Default to search the front value first
            # TODO Make this more intelligent
            #
            value_left = self.get_var_value(
                var_name        = var,
                var_expressions = var_expressions,
                data_type       = data_type,
                left_or_right   = MatchExpression.TERM_LEFT
            )
            value_right = self.get_var_value(
                var_name        = var,
                var_expressions = var_expressions,
                data_type       = data_type,
                left_or_right   = MatchExpression.TERM_RIGHT
            )

            if value_left or value_right:
                lg.Log.debug(
                    str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': For var "' + str(var) + '" found values ' + str([value_left, value_right])
                )
                try:
                    if data_type not in self.map_vartype_to_regex.keys():
                        raise Exception('Unrecognized type "' + str(data_type) + '".')
                    elif data_type == MatchExpression.MEX_TYPE_INT:
                        if value_left:
                            value_left = int(value_left)
                        if value_right:
                            value_right = int(value_right)
                        var_values[var] = (value_left, value_right)
                    elif data_type == MatchExpression.MEX_TYPE_FLOAT:
                        if value_left:
                            value_left = float(value_left)
                        if value_right:
                            value_right = float(value_right)
                        var_values[var] = (value_left, value_right)
                    else:
                        if value_left:
                            value_left = str(value_left)
                        if value_right:
                            value_right = str(value_right)
                        var_values[var] = (value_left, value_right)
                except Exception as ex_int_conv:
                    errmsg = str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                             + ': Failed to extract variable "' + str(var)\
                             + '" from sentence "' + str(self.sentence)\
                             + '". Exception ' + str(ex_int_conv) + '.'
                    lg.Log.warning(errmsg)

        lg.Log.debug(
            str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': For sentence "' + str(self.sentence) + '" var values ' + str(var_values)
        )

        return var_values

    def get_var_value_regex(
            self,
            patterns_list,
            var_name
    ):
        lg.Log.debug(
            str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': For var "' + str(var_name)
            + '" using match patterns list ' + str(patterns_list)
        )
        if patterns_list is None:
            lg.Log.error(
                str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                + ': No patterns list provided for string "' + str(self.sentence)
                + '", var name "' + str(var_name) + '".'
            )
            return None

        for pattern in patterns_list:
            m = re.match(pattern=pattern, string=self.sentence)
            if m:
                lg.Log.debug(
                    str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': For var "' + str(var_name) + '" using pattern "' + str(pattern)
                    + '", found groups ' + str(m.groups())
                )
                return m
        return None

    def get_pattern_list(
            self,
            data_type,
            var_expressions,
            left_or_right
    ):
        if not self.case_sensitive:
            var_expressions = var_expressions.lower()

        patterns_list = []
        try:
            fix_list = self.map_vartype_to_regex[data_type][left_or_right]
            for pat in fix_list:
                if left_or_right == MatchExpression.TERM_LEFT:
                    patterns_list.append(
                        pat + '[ ]*(' + str(var_expressions) + ').*'
                    )
                else:
                    patterns_list.append(
                        '.*(' + var_expressions + ')[ ]*' + pat
                    )
            return patterns_list
        except Exception as ex:
            errmsg = str(MatchExpression.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ': Exception "' + str(ex)\
                     + '" getting ' + str(left_or_right) + ' pattern list for var expressions "'\
                     + str(var_expressions) + '", data type "' + str(data_type) + '".'
            lg.Log.error(errmsg)
            raise Exception(errmsg)

    def get_var_value(
            self,
            var_name,
            var_expressions,
            data_type,
            left_or_right
    ):
        var_expressions = var_expressions.lower()

        try:
            patterns_list = self.get_pattern_list(
                data_type = data_type,
                var_expressions = var_expressions,
                left_or_right   = left_or_right
            )
        except Exception as ex:
            errmsg = str(MatchExpression.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ': Exception "' + str(ex)\
                     + '" getting ' + str(left_or_right) + ' pattern list for var name "' + str(var_name)\
                     + '", sentence "' + str(self.sentence) + '", var expressions "' + str(var_expressions)\
                     + '", data type "' + str(data_type) + '".'
            lg.Log.error(errmsg)
            return None

        m = self.get_var_value_regex(
            # Always check float first
            patterns_list = patterns_list,
            var_name      = var_name
        )

        group_position = 1
        if left_or_right == MatchExpression.TERM_RIGHT:
            group_position = 2

        if m:
            if len(m.groups()) >= group_position:
                return m.group(group_position)
            else:
                warn_msg = \
                    str(MatchExpression.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': For ' + str(left_or_right) + ' match, expected at least ' + str(group_position)\
                    + ' match groups for var name "' + str(var_name)\
                    + '", string "' + str(self.sentence) + '", var expressions "' + str(var_expressions)\
                    + '", data type "' + str(data_type) + '" but got groups ' + str(m.groups()) + '.'
                lg.Log.warning(warn_msg)
        return None

    def get_params(
            self,
            return_one_value = True,
            return_value_priority = TERM_LEFT
    ):
        #
        # Extract variables from question
        #
        params_dict = self.extract_variable_values()

        if return_one_value:
            for key in params_dict.keys():
                values = params_dict[key]
                index_priority_order = (0,1)
                if return_value_priority == MatchExpression.TERM_RIGHT:
                    index_priority_order = (1,0)
                if values[index_priority_order[0]] is not None:
                    params_dict[key] = values[index_priority_order[0]]
                elif values[index_priority_order[1]] is not None:
                    params_dict[key] = values[index_priority_order[1]]
                else:
                    params_dict[key] = None

        return params_dict

    
if __name__ == '__main__':
    # cf_obj = cf.Config.get_cmdline_params_and_init_config_singleton(
    #     Derived_Class = cf.Config
    # )
    lg.Log.DEBUG_PRINT_ALL_TO_SCREEN = True
    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_IMPORTANT

    tests = [
        {
            # We also use the words 'test&escape' and ';' (clashes with var separator
            # but works because we escape the word using '\\;')
            # to detect diameter.
            # Need to escape special mex characters like ; if used as expression
            'mex': 'r, float, radius & r  ;'
                   + 'd, float, diameter & d & test\\&escape & \\; & + & * &\\&   ;   ',
            'sentences': [
                'What is the volume of a sphere of radius 5.88?',
                'What is the volume of a sphere of radius 5.88 and 4.9 diameter?',
                'What is the volume of a sphere of radius 5.88 and 33.88 test&escape?',
                'What is the volume of a sphere of radius 5.88, 33.88;?',
                # When stupid user uses '+' to detect a param, should also work, but not recommended
                'What is the volume of a sphere of radius 5.88, +33.88?',
                # Using '*' to detect diameter
                'What is the volume of a sphere of radius 5.88, 33.88*?',
                # Using '&' to detect diameter
                'What is the volume of a sphere of radius 5.88, 33.88&?',
                # Should not detect diameter because we say to look for 'd', not any word ending 'd'
                # But because we have to handle languages like Chinese/Thai where there is no word
                # separator, we allow this and the diameter will be detected
                'What is the volume of a sphere of radius 5.88 and 33.88?',
                # Should not be able to detect now diameter
                'What is the volume of a sphere of radius 5.88 & 33.88?'
            ]
        },
        {
            'mex': 'dt,datetime,   ;   email,email,   ;   inc, float, inc & inch & inches',
            'sentences': [
                'What is -2.6 inches? 20190322 05:15 send to me@abc.com.',
                'What is +1.2 inches? 2019-03-22 05:15 you@email.ua ?',
                '2019-03-22: u_ser-name.me@gmail.com is my email',
                '이멜은u_ser-name.me@gmail.com',
                'u_ser-name.me@gmail.invalid is my email'
            ]
        },
        {
            'mex': 'dt, datetime,   ;   acc, number, 계정 & 번호   ;   '
                   + 'm, int, 월   ;   d, int, 일   ;   t, time, 에   ;'
                   + 'amt, float, 원   ;   bal, float, 잔액   ',
            'sentences': [
                '2020-01-01: 번호 0011 계정은 9 월 23 일 10:12 에 1305.67 원, 잔액 9999.77.',
                '20200101 xxx: 번호 0011 계정은 8 월 24 일 10:12 에 원 1305.67, 9999.77 잔액.',
                'AAA 2020-01-01 11:52:22: 번호 0022 계정은 7 월 25 일 10:15:55 에 1405.78 원, 잔액 8888.77.',
                '2020-01-01: 번호 0033 계정은 6 월 26 일 完成23:24 에 1505.89 원, 잔액 7777.77.',
                '2020-01-01: 번호 0044 계정은 5 월 27 일 完成23:24:55 에 5501.99 원, 잔액 6666.77.',
                '2020-01-01: 번호0055계정은4월28일11:37에1111.22원，잔액5555.77.',
                '2020-01-01: 번호0066계정은3월29일11:37:55에2222.33원，잔액4444.77',
                '2020-01-01: 번호0777계정은30일 完成11:38:55에3333.44원'
            ]
        }
    ]

    for test in tests:
        pattern = test['mex']
        sentences = test['sentences']

        for sent in sentences:
            cmobj = MatchExpression(
                pattern  = pattern,
                sentence = sent
            )
            params_all = cmobj.get_params(
                return_one_value = False,
                return_value_priority = MatchExpression.TERM_LEFT
            )
            #print(params_all)

            params_one = cmobj.get_params(
                return_one_value = True,
                return_value_priority = MatchExpression.TERM_LEFT
            )
            print(params_one)
