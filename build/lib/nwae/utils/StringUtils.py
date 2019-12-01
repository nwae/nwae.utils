#!/usr/bin/python
# -*- coding: utf-8 -*-

import re


class StringUtils(object):

    def __init__(self):
        return

    @staticmethod
    def trim(string):
        try:
            # Remove only beginning/ending space, tab, newline, return carriage
            s = re.sub('[ \t\n\r]+$', '', re.sub('^[ \t\n\r]+', '', string))
            return s
        except Exception as ex:
            print(
                str(StringUtils.__name__) + ': trim "' + str(string) + ' + " exception "' + str(ex) + '".'
            )
            return string

    @staticmethod
    def remove_newline(string, replacement=''):
        try:
            s = re.sub('[\n\r]+', replacement, string)
            return s
        except Exception as ex:
            print(
                str(StringUtils.__name__) + ': remove_newline "' + str(string) + ' + " exception "' + str(ex) + '".'
            )
            return string

    @staticmethod
    def split(string, split_word):
        escape_char = '\\'

        if string is None:
            return []
        len_sw = len(split_word)
        if len_sw == 0:
            return [string]

        split_arr = []
        last_start_pos = 0
        for i in range(len(string)):
            # Do nothing if in the middle of the split word
            if i<last_start_pos:
                continue
            if i+len_sw<=len(string):
                if string[i:(i+len_sw)] == split_word:
                    if (i>0) and (string[i-1]!=escape_char):
                        # Extract this word
                        s_extract = string[last_start_pos:i]
                        # Now remove the escape character from the split out word
                        s_extract = re.sub(pattern='\\\\'+split_word, repl=split_word, string=s_extract)
                        split_arr.append(
                            StringUtils.trim(s_extract)
                        )
                        # Move to new start position
                        last_start_pos = i + len_sw
                        # print('New start position = ' + str(last_start_pos)+ ', for string "' + str(string[last_start_pos:]) + '".')
        # Always add the last word, even though it is empty due to common expected behavior
        final_extract = string[last_start_pos:len(string)]
        # Now remove the escape character from the split out word
        final_extract = re.sub(pattern='\\\\' + split_word, repl=split_word, string=final_extract)
        split_arr.append(final_extract)
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
        # Split word = '', so should return the whole string back
        ('first; sec\\;ond ;\\;third;fourth', ''),
        # Should not split 'sec;ond' into 'sec' & 'ond'
        ('first; sec\\;ond ;\\;third;fourth', ';'),
        ('first; sec\\;ond ;\\;third;fourth;', ';'),
        ('first NEXT WORD sec\\NEXT WORD ond NEXT WORD\\;thirdNEXT WORDfourth', 'NEXT WORD'),
        ('firstNEXT WORD sec\\NEXT WORDond NEXT WORD\\NEXT WORDthird NEXT WORD fourthNEXT WORD', 'NEXT WORD'),
        ('diameter&d&test\\&escape', '&')
    ]
    for s in arr:
        # print('Before split: ' + str(s))
        print('After split:  ' + str(StringUtils.split(string=s[0], split_word=s[1])))

