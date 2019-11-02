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

    TERM_FRONT = 'front'
    TERM_BACK  = 'back'
    #
    # Mapping of regular expressions to data type, you may pass in your custom one at constructor
    #
    MAP_VARTYPE_REGEX = {
        MEX_TYPE_FLOAT: {
            TERM_FRONT: [
                # In front of variable expression
                '.*[^0-9\-]+([+\-]*[0-9]+[.][0-9]*)',
                # In front of variable expression at the start of sentence
                '^([+\-]*[0-9]+[.][0-9]*)'
            ],
            TERM_BACK: [
                # After or at the back of variable expression
                '([+\-]*[0-9]+[.][0-9]*).*'
            ]
        },
        MEX_TYPE_INT: {
            TERM_FRONT: [
                # In front of variable expression
                '.*[^0-9\-]+([+\-]*[0-9]+)',
                # In front of variable expression at the start of sentence
                '^([+\-]*[0-9]+)'
            ],
            TERM_BACK: [
                # After or at the back of variable expression
                '([+\-]*[0-9]+).*'
            ]
        },
        MEX_TYPE_NUMBER: {
            TERM_FRONT: [
                # In front of variable expression
                '.*[^0-9\-]+([+\-]*[0-9]+)',
                # In front of variable expression at the start of sentence
                '^([+\-]*[0-9]+)'
            ],
            TERM_BACK: [
                # After or at the back of variable expression
                '([+\-]*[0-9]+).*'
            ]
        },
        MEX_TYPE_TIME: {
            TERM_FRONT: [
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
            TERM_BACK: [
                # HHMMSS. After or at the back of variable expression
                '([0-9]+[:][0-9]+[:][0-9]+).*',
                # HHMM. After or at the back of variable expression
                '([0-9]+[:][0-9]+).*'
            ]
        },
        MEX_TYPE_DATETIME: {
            TERM_FRONT: [
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
            TERM_BACK: [
                # "yyyymmdd HHMMSS". After or at the back of variable expression
                '([0-9]{4}[-]*[0-1][0-9][-*][0-3][0-9][ ]+[0-9]+[:][0-9]+[:][0-9]+).*',
                # "yyyymmdd HHMM". After or at the back of variable expression
                '([0-9]{4}[-]*[0-1][0-9][-*][0-3][0-9][ ]+[0-9]+[:][0-9]+).*',
                # "yyyymmdd"". After or at the back of variable expression
                '([0-9]{4}[-]*[0-1][0-9][-*][0-3][0-9]).*',
            ]
        },
        MEX_TYPE_EMAIL: {
            TERM_FRONT: [
                # In front of variable expression
                '.*[^' + USERNAME_CHARS + ']+' + '([' + USERNAME_CHARS + ']+' + '[@][a-zA-Z0-9]+[.][a-zA-Z]+)',
                # In front of variable expression at the start of sentence
                '^([' + USERNAME_CHARS + ']+' + '[@][a-zA-Z0-9]+[.][a-zA-Z]+)'
            ],
            TERM_BACK: [
                # After or at the back of variable expression
                '([' + USERNAME_CHARS + ']+' + '[@][a-zA-Z0-9]+[.][a-zA-Z]+).*'
            ]
        }
    }

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
    @staticmethod
    def decode_vars_object_str(
            s
    ):
        try:
            var_encoding = {}

            # Use our own split function that will ignore escaped built-in separator
            # Here we split "m,float,mass&m;c,float,light&speed" into ['m,float,mass&m', 'c,float,light&speed']
            str_encoding = su.StringUtils.split(
                string = s,
                split_word = MatchExpression.MEX_VAR_DEFINITION_SEPARATOR
            )
            for varset in str_encoding:
                # Use our own split function that will ignore escaped built-in separator
                # Here we split 'm,float,mass&m' into ['m','float','mass&m']
                var_desc = su.StringUtils.split(
                    string = varset,
                    split_word = MatchExpression.MEX_VAR_DESCRIPTION_SEPARATOR
                )

                part_var_id = var_desc[0]
                part_var_type = var_desc[1]
                part_var_expressions = var_desc[2]

                var_encoding[part_var_id] = {
                    # Extract 'float' from ['m','float','mass&m']
                    MatchExpression.MEX_OBJECT_VARS_TYPE: part_var_type,
                    # Extract ['mass','m'] from 'mass&m'
                    MatchExpression.MEX_OBJECT_VARS_EXPRESIONS: su.StringUtils.split(
                        string = part_var_expressions,
                        split_word = MatchExpression.MEX_VAR_EXPRESSIONS_SEPARATOR
                    )
                }
                lg.Log.info(
                    str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': Successfully decoded vars object item "'
                    + str(part_var_id) + '": ' + str(var_encoding[var_desc[0]])
                )
            return var_encoding
        except Exception as ex:
            errmsg = str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Failed to get var encoding for "' + str(s) + '". Exception ' + str(ex) + '.'
            lg.Log.error(errmsg)
            return None

    #
    # Extract variables from string
    #
    @staticmethod
    def extract_variable_values(
            s,
            var_encoding,
            map_vartype_to_regex
    ):
        s = str(s).lower()

        lg.Log.debug(
            str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Extracting vars from "' + str(s) + '", using encoding ' + str(var_encoding)
        )

        var_values = {}

        # Look one by one
        for var in var_encoding.keys():
            var_values[var] = None
            # Get the names and join them using '|' for matching regex
            var_expressions = '|'.join(var_encoding[var][MatchExpression.MEX_OBJECT_VARS_EXPRESIONS])
            data_type = var_encoding[var][MatchExpression.MEX_OBJECT_VARS_TYPE]

            #
            # Default to search the front value first
            # TODO Make this more intelligent
            #
            value = MatchExpression.get_var_value_front(
                var_name = var,
                string = s,
                var_expressions = var_expressions,
                data_type = data_type,
                map_vartype_to_regex = map_vartype_to_regex
            )
            if not value:
                value = MatchExpression.get_var_value_back(
                    var_name = var,
                    string = s,
                    var_expressions = var_expressions,
                    data_type = data_type,
                    map_vartype_to_regex = map_vartype_to_regex
                )

            if value:
                lg.Log.debug(
                    str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': For var "' + str(var) + '" found value ' + str(value)
                )
                try:
                    if data_type not in map_vartype_to_regex.keys():
                        raise Exception('Unrecognized type "' + str(data_type) + '".')
                    elif data_type == MatchExpression.MEX_TYPE_INT:
                        var_values[var] = int(value)
                    elif data_type == MatchExpression.MEX_TYPE_FLOAT:
                        var_values[var] = float(value)
                    else:
                        var_values[var] = str(value)
                except Exception as ex_int_conv:
                    errmsg = str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                             + ': Failed to extract variable "' + str(var) + '" from "' + str(s)\
                             + '". Exception ' + str(ex_int_conv) + '.'
                    lg.Log.warning(errmsg)

        lg.Log.debug(
            str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': For s "' + str(s) + '" var values ' + str(var_values)
        )

        return var_values

    @staticmethod
    def get_var_value_regex(
            patterns_list,
            var_name,
            string
    ):
        lg.Log.debug(
            str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': For var "' + str(var_name)
            + '" using match patterns list ' + str(patterns_list)
        )
        if patterns_list is None:
            lg.Log.error(
                str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                + ': No patterns list provided for string "' + str(string)
                + '", var name "' + str(var_name) + '".'
            )
            return None

        for pattern in patterns_list:
            m = re.match(pattern=pattern, string=string)
            if m:
                lg.Log.debug(
                    str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': For var "' + str(var_name) + '" using pattern "' + str(pattern)
                    + '", found groups ' + str(m.groups())
                )
                return m
        return None

    @staticmethod
    def get_var_value_front(
            var_name,
            string,
            var_expressions,
            data_type,
            map_vartype_to_regex
    ):
        var_expressions = var_expressions.lower()

        patterns_list = []
        try:
            fix_list = map_vartype_to_regex[data_type][MatchExpression.TERM_FRONT]
            for pat_front in fix_list:
                patterns_list.append(pat_front + '[ ]*(' + str(var_expressions) + ').*')
        except Exception as ex:
            errmsg = str(MatchExpression.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ': Exception "' + str(ex)\
                     + '" getting pattern list for front var value for var name "' + str(var_name)\
                     + '", string "' + str(string) + '", var expressions "' + str(var_expressions)\
                     + '", data type "' + str(data_type) + '".'
            lg.Log.error(errmsg)
            return None

        m = MatchExpression.get_var_value_regex(
            # Always check float first
            patterns_list = patterns_list,
            var_name      = var_name,
            string        = string
        )

        if m:
            if len(m.groups()) >= 1:
                return m.group(1)
            else:
                warn_msg = \
                    str(MatchExpression.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': Var Front. Expected 2 match groups for var name "' + str(var_name)\
                    + '", string "' + str(string) + '", var expressions "' + str(var_expressions)\
                    + '", data type "' + str(data_type) + '" but got groups ' + str(m.groups()) + '.'
                lg.Log.warning(warn_msg)
        return None

    @staticmethod
    def get_var_value_back(
            var_name,
            string,
            var_expressions,
            data_type,
            map_vartype_to_regex
    ):
        var_expressions = var_expressions.lower()

        patterns_list = []
        try:
            fix_list = map_vartype_to_regex[data_type][MatchExpression.TERM_BACK]
            for pat_back in fix_list:
                patterns_list.append('.*(' + var_expressions + ')[ ]*' + pat_back)
        except Exception as ex:
            errmsg = str(MatchExpression.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ': Exception "' + str(ex)\
                     + '" getting pattern list for back var value for var name "' + str(var_name)\
                     + '", string "' + str(string) + '", var expressions "' + str(var_expressions)\
                     + '", data type "' + str(data_type) + '".'
            lg.Log.error(errmsg)
            return None

        m = MatchExpression.get_var_value_regex(
            # Always check float first
            patterns_list = patterns_list,
            var_name      = var_name,
            string        = string
        )
        if m:
            if len(m.groups()) >= 2:
                return m.group(2)
            else:
                warn_msg = \
                    str(MatchExpression.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': Var Back. Expected 2 match groups for var name "' + str(var_name)\
                    + '", string "' + str(string) + '", var type names "' + str(var_type_names)\
                    + '", data type "' + str(data_type) + '" but got groups ' + str(m.groups()) + '.'
                lg.Log.warning(warn_msg)
        return None

    def __init__(
            self,
            pattern,
            sentence,
            map_vartype_to_regex = MAP_VARTYPE_REGEX
    ):
        self.pattern = pattern
        self.sentence = sentence
        self.map_vartype_to_regex = map_vartype_to_regex
        lg.Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Pattern "' + str(self.pattern)
            + '" question "' + str(self.sentence) + '".'
        )
        #
        # Decode the model variables
        #
        self.mex_obj_vars = None
        self.__decode_str()
        return

    def __decode_str(self):
        lg.Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Mex pattern: ' + str(self.pattern)
        )
        self.mex_obj_vars = MatchExpression.decode_vars_object_str(
            s = self.pattern
        )
        lg.Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Model Object vars: ' + str(self.mex_obj_vars)
        )
        return

    def get_params(self):
        #
        # Extract variables from question
        #
        var_values = MatchExpression.extract_variable_values(
            s = self.sentence,
            var_encoding = self.mex_obj_vars,
            map_vartype_to_regex = self.map_vartype_to_regex
        )

        return var_values

    
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
            'mex': 'r,float,radius&r;d,float,diameter&d&test\\&escape&\\;',
            'sentences': [
                'What is the volume of a sphere of radius 5.88?',
                'What is the volume of a sphere of radius 5.88 and 4.9 diameter?',
                'What is the volume of a sphere of radius 5.88 and 33.88 test&escape?',
                'What is the volume of a sphere of radius 5.88, 33.88;?',
                # Should not detect diameter because we say to look for 'd', not any word ending 'd'
                # But because we have to handle languages like Chinese/Thai where there is no word
                # separator, we allow this and the diameter will be detected
                'What is the volume of a sphere of radius 5.88 and 33.88?',
            ]
        },
        {
            'mex': 'dt,datetime,;email,email,;inc,float,inc&inch&inches',
            'sentences': [
                'What is -2.6 inches? 20190322 05:15 send to me@abc.com.',
                'What is +1.2 inches? 2019-03-22 05:15 you@email.ua ?',
                '2019-03-22: u_ser-name.me@gmail.com is my email',
                '이멜은u_ser-name.me@gmail.com',
                'u_ser-name.me@gmail.invalid is my email'
            ]
        },
        {
            'mex': 'dt,datetime,;acc,number,계정&번호;m,int,월;d,int,일;t,time,에;amt,float,원;bal,float,잔액',
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
            params = cmobj.get_params()
            print(params)
