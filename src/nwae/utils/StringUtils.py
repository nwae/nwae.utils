#!/usr/bin/python
# -*- coding: utf-8 -*-

import re


class StringUtils(object):

    def __init__(self):
        return

    @staticmethod
    def trim(str):
        # Remove only beginning/ending space, tab, newline, return carriage
        s = re.sub('[ \t\n\r]+$', '', re.sub('^[ \t\n\r]+', '', str))
        return s

    @staticmethod
    def remove_newline(str, replacement=''):
        s = re.sub('[\n\r]+', replacement, str)
        return s

    @staticmethod
    def split(str, split_word):
        escape_char = '\\'

        if str is None:
            return []
        len_sw = len(split_word)
        if len_sw == 0:
            return [str]

        split_arr = []
        last_start_pos = 0
        for i in range(len(str)):
            # Do nothing if in the middle of the split word
            if i<last_start_pos:
                continue
            if i+len_sw<=len(str):
                if str[i:(i+len_sw)] == split_word:
                    if (i>0) and (str[i-1]!=escape_char):
                        # Extract this word
                        s_extract = str[last_start_pos:i]
                        # Now remove the escape character from the split out word
                        s_extract = re.sub(pattern='\\\\'+split_word, repl=split_word, string=s_extract)
                        split_arr.append(
                            StringUtils.trim(s_extract)
                        )
                        # Move to new start position
                        last_start_pos = i + len_sw
        if last_start_pos < len(str)-1:
            split_arr.append(str[last_start_pos:len(str)])
        return split_arr

if __name__ == '__main__':
    arr = [
        '  Privet Mir   ',
        '  \n\r Privet Mir   ',
        '  \n Privet Mir   ',
        '  \r Privet Mir   \n\r ',
        '  Privet Mir   \n ',
        '  Privet Mir   \r ',
        ' \t  Privet Mir  \t  ',
        '  Privet Mir 1  \n\r',
        '\t Privet Mir 1   \n\r   Privet Mir 2 \n\rPrivet Mir3  \n\r'
    ]

    for s in arr:
        # Demonstrating that newline is also removed
        ss = StringUtils.trim(s)
        # ss = StringUtils.remove_newline(ss)
        print('[' + ss + ']')

    split_word = ';'
    arr = [
        ('first; sec\\;ond ;\\;third;fourth', ';'),
        ('first; sec\\;ond ;\\;third;fourth;', ';'),
        ('first NEXT WORD sec\\NEXT WORD ond NEXT WORD\\;thirdNEXT WORDfourth', 'NEXT WORD'),
        ('firstNEXT WORD sec\\NEXT WORDond NEXT WORD\\NEXT WORDthird NEXT WORD fourthNEXT WORD', 'NEXT WORD'),
    ]
    for s in arr:
        # print('Before split: ' + str(s))
        print('After split:  ' + str(StringUtils.split(str=s[0], split_word=s[1])))

