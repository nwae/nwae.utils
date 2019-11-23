# -*- coding: utf-8 -*-
import sys
import nwae.utils.StringUtils as su


class CmdLine:

    @staticmethod
    def get_cmdline_params(
            pv_default = None
    ):
        pv = {}
        if type(pv_default) is dict:
            for k in pv_default.keys():
                pv[k] = pv_default[k]

        # Config file on command line will overwrite default config file
        args = sys.argv
        for arg in args:
            arg_split = arg.split('=')
            if len(arg_split) == 2:
                param = arg_split[0].lower()
                value = su.StringUtils.trim(arg_split[1])
                if value != '':
                    pv[param] = value

        return pv


if __name__ == '__main__':
    print(CmdLine.get_cmdline_params())
    print(CmdLine.get_cmdline_params(pv_default={'a':99, 'c':'Test', 'd':888}))

