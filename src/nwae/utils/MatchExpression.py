# -*- coding: utf-8 -*-

import nwae.utils.Log as lg
from inspect import getframeinfo, currentframe
import re


#
# Higher Level Abstraction to re.match() to extract parameters
#
# Language
#   var_1;var_2;var_3;..
# where
#   var_x = <var_name>,<var_type>,<expression_1>&<expression_2>&...
#
# <var_type> can be
#    - int
#    - float
#    - number (string instead of integer and will not remove leading 0's)
#    - time (12:30:55, 23:59)
#
class MatchExpression:
    
    DEFAULT_NUMBER_ROUNDING = 5

    MEX_ENCODE_STR    = 'encode_str'
    MEX_OBJECT_VARS   = 'vars'

    MEX_OBJECT_VARS_TYPE = 'type'
    MEX_OBJECT_VARS_NAMES = 'names'

    # We use '-*-' to open and close the encoding language
    MEX_ENCODING_CHARS_START_END = '[-][*][-](.*)[-][*][-]'

    # Separates the vars and answer object. E.g.
    #    vars==m,float,mass&m;c,float,light&speed::answer==$$m * ($$c * $$c)
    MEX_OBJECT_SEPARATOR = '::'
    MEX_OBJECT_DEFINITION_SYMBOL = '=='
    # Separates the different variables definition. e.g. 'm,float,mass&m;c,float,light&speed'
    MEX_VAR_DEFINITION_SEPARATOR = ';'
    # Separates the description of the same variable. e.g. 'm,float,mass&m'
    MEX_VAR_DESCRIPTION_SEPARATOR = ','
    # Separates the names of a variable. e.g. 'mass&m'
    MEX_VAR_NAMES_SEPARATOR = '&'
    MEX_VAR_MARKUP_IN_QUESTION = '[$]{2}'

    MEX_TYPE_FLOAT  = 'float'
    MEX_TYPE_INT    = 'int'
    # String format and will not remove leading 0's
    MEX_TYPE_NUMBER = 'number'
    # e.g. 10:12:36, 12:15
    MEX_TYPE_TIME   = 'time'
    
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

            # Here we split "m,float,mass&m;c,float,light&speed" into ['m,float,mass&m', 'c,float,light&speed']
            str_encoding = s.split(MatchExpression.MEX_VAR_DEFINITION_SEPARATOR)
            for varset in str_encoding:
                # Here we split 'm,float,mass&m' into ['m','float','mass&m']
                var_desc = varset.split(MatchExpression.MEX_VAR_DESCRIPTION_SEPARATOR)

                part_var_id = var_desc[0]
                part_var_type = var_desc[1]
                part_var_names = var_desc[2]

                var_encoding[part_var_id] = {
                    # Extract 'float' from ['m','float','mass&m']
                    MatchExpression.MEX_OBJECT_VARS_TYPE: part_var_type,
                    # Extract ['mass','m'] from 'mass&m'
                    MatchExpression.MEX_OBJECT_VARS_NAMES: part_var_names.split(
                        sep = MatchExpression.MEX_VAR_NAMES_SEPARATOR
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
            var_encoding
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
            names = '|'.join(var_encoding[var][MatchExpression.MEX_OBJECT_VARS_NAMES])
            data_type = var_encoding[var][MatchExpression.MEX_OBJECT_VARS_TYPE]

            #
            # Default to search the front value first
            # TODO Make this more intelligent
            #
            value = MatchExpression.get_var_value_front(
                var_name = var,
                string = s,
                var_type_names = names,
                data_type = data_type
            )
            if not value:
                value = MatchExpression.get_var_value_back(
                    var_name = var,
                    string = s,
                    var_type_names = names,
                    data_type = data_type
                )

            if value:
                lg.Log.debug(
                    str(MatchExpression.__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': For var "' + str(var) + '" found value ' + str(value)
                )
                try:
                    if data_type == MatchExpression.MEX_TYPE_INT:
                        var_values[var] = int(value)
                    elif data_type == MatchExpression.MEX_TYPE_FLOAT:
                        var_values[var] = float(value)
                    elif data_type == MatchExpression.MEX_TYPE_TIME:
                        var_values[var] = value
                    else:
                        raise Exception('Unrecognized type "' + str(data_type) + '".')
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
            var_type_names,
            data_type
    ):
        var_type_names = var_type_names.lower()
        # Always check float first
        pattern_check_front_float = '.*[^0-9\-]+([+\-]*[0-9]+[.][0-9]*)[ ]*(' + var_type_names + ').*'
        pattern_check_front_float_start = '^([+\-]*[0-9]+[.][0-9]*)[ ]*(' + var_type_names + ').*'
        pattern_check_front_int = '.*[^0-9\-]+([+\-]*[0-9]+)[ ]*(' + var_type_names + ').*'
        pattern_check_front_int_start = '^([+\-]*[0-9]+)[ ]*(' + var_type_names + ').*'
        # Time pattern. e.g. 12:30:59, 23:45
        # Check HHMMSS first, if that fails then only HHMM
        pattern_check_front_time_HHMMSS = '.*[^0-9]+([0-9]+[:][0-9]+[:][0-9]+)[ ]*(' + var_type_names + ').*'
        pattern_check_front_time_start_HHMMSS = '^([0-9]+[:][0-9]+[:][0-9]+)[ ]*(' + var_type_names + ').*'
        pattern_check_front_time_HHMM = '.*[^0-9]+([0-9]+[:][0-9]+)[ ]*(' + var_type_names + ').*'
        pattern_check_front_time_start_HHMM = '^([0-9]+[:][0-9]+)[ ]*(' + var_type_names + ').*'

        patterns_list = None
        if data_type in (MatchExpression.MEX_TYPE_FLOAT, MatchExpression.MEX_TYPE_INT):
            patterns_list = (
                    pattern_check_front_float, pattern_check_front_float_start,
                    pattern_check_front_int, pattern_check_front_int_start
            )
        elif data_type == MatchExpression.MEX_TYPE_TIME:
            patterns_list = (
                pattern_check_front_time_HHMMSS, pattern_check_front_time_start_HHMMSS,
                pattern_check_front_time_HHMM, pattern_check_front_time_start_HHMM
            )

        m = MatchExpression.get_var_value_regex(
            # Always check float first
            patterns_list = patterns_list,
            var_name      = var_name,
            string        = string
        )
        if m:
            return m.group(1)
        return None

    @staticmethod
    def get_var_value_back(
            var_name,
            string,
            var_type_names,
            data_type
    ):
        var_type_names = var_type_names.lower()
        # Always check float first
        pattern_check_back_float = '.*(' + var_type_names + ')[ ]*([+\-]*[0-9]+[.][0-9]*).*'
        pattern_check_back_int = '.*(' + var_type_names + ')[ ]*([+\-]*[0-9]+).*'
        # Time pattern. e.g. 12:30:59, 23:45
        # Check HHMMSS first, if that fails then only HHMM
        pattern_check_back_time_HHMMSS = '.*(' + var_type_names + ')[ ]*([0-9]+[:][0-9]+[:][0-9]+).*'
        pattern_check_back_time_HHMM = '.*(' + var_type_names + ')[ ]*([0-9]+[:][0-9]+).*'

        patterns_list = None
        if data_type in (MatchExpression.MEX_TYPE_FLOAT, MatchExpression.MEX_TYPE_INT):
            patterns_list = (pattern_check_back_float, pattern_check_back_int)
        elif data_type == MatchExpression.MEX_TYPE_TIME:
            patterns_list = (pattern_check_back_time_HHMMSS, pattern_check_back_time_HHMM)

        m = MatchExpression.get_var_value_regex(
            # Always check float first
            patterns_list = patterns_list,
            var_name      = var_name,
            string        = string
        )
        if m:
            return m.group(2)
        return None

    def __init__(
            self,
            encoding_str,
            sentence
    ):
        self.encoding_str = encoding_str
        self.sentence = sentence
        lg.Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Daehua Model Encoding "' + str(self.encoding_str)
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
            + ': Mex Encoding string: ' + str(self.encoding_str)
        )
        self.mex_obj_vars = MatchExpression.decode_vars_object_str(
            s = self.encoding_str
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
            var_encoding = self.mex_obj_vars
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
            'mex': 'r,float,radius&r;d,float,diameter&d',
            'sentences': [
                'What is the volume of a sphere of radius 5.88?'
            ]
        },
        {
            'mex': 'id,float,id&indo',
            'sentences': [
                'What is -2.6 indo odds?',
                'What is +1.2 indo odds?'
            ]
        },
        {
            'mex': 'acc,int,尾号&账号;m,int,月;d,int,日;t,time,完成;amt,float,民币&币;bal,float,余额',
            'sentences': [
                '【中国农业银行】您尾号0579账户10月17日09:27完成代付交易人民币2309.95，余额2932.80。',
                '【中国农业银行】您尾号0579账户10月17日09:27:55完成代付交易人民币2309.95，余额2932.80。',
                '【中国农业银行】您尾号0579账户10月17日完成09:27代付交易人民币2309.95，余额2932.80。',
                '【中国农业银行】您尾号0579账户10月17日完成09:27:55代付交易人民币2309.95，余额2932.80。',
                '【中国农业银行】 您尾号 0579 账户 10月 17日 完成 09:27 代付交易 人民币 2309.95，余额 2932.80。',
                '【中国农业银行】 您尾号  0579 账户 10月 17日 完成 09:27:55 代付交易 人民币 2309.95，余额 2932.80。',
            ]
        }
    ]

    for test in tests:
        encoding = test['mex']
        sentences = test['sentences']

        for sent in sentences:
            cmobj = MatchExpression(
                encoding_str = encoding,
                sentence     = sent
            )
            params = cmobj.get_params()
            print(params)
