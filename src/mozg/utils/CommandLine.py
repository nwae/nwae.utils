#!/usr/bin/python
# -*- coding: utf-8 -*-

import mozg.common.util.StringUtils as su
import re
import mozg.common.data.Account as ac
import mozg.common.data.Campaign as cp
import mozg.common.data.Bot as bt
import pandas as pd
import mozg.common.bot.BotIntentAnswer as botia


class CommandLine:

    DF_COL_NAME = 'name'
    DF_COL_ID = 'id'
    DF_COL_LANG = 'lang'

    @staticmethod
    def get_parameters_to_run_bot(
            db_profile
    ):
        [accountId, accountName, dummyVar] = [None, None, None]
        # Only used for us to map to brand/lang
        # [campaignId, campaignName] = [None, None]
        [botId, botName, botLang] = [None, None, None]

        while accountId is None:
            [accountId, accountName, dummyVar] = CommandLine.get_user_input_account(
                db_profile=db_profile,
                param_name='Account'
            )

        while botId is None:
            [botId, botName, botLang] = CommandLine.get_user_input_bot(
                db_profile=db_profile,
                param_name='Bot',
                account_id=accountId
            )

        botLang = bt.Bot.get_bot_lang(language=botLang)

        botkey = bt.Bot.get_bot_key(
            db_profile=db_profile,
            account_id=accountId,
            bot_id=botId,
            lang=botLang
        )

        return (accountId, botId, botLang, botkey)

    @staticmethod
    def get_user_filename():
        ui = None
        while True:
            ui = input('Enter Filename (\'m\' to return to Main Menu): ')
            if ui == 'm':
                ui = None
                break
            elif su.StringUtils.trim(ui).__len__() == 0:
                print('File name is empty!')
                continue
            else:
                break
        return ui

    @staticmethod
    def get_user_input_language():
        ui_lang = None
        while True:
            print('Pick Language:')
            print('  1: CNY')
            print('  2: THB')
            print('  (Coming soon VND)')
            print('  m: Back to Main Menu')
            print('                ')
            ui_lang = input('Enter Language: ')
            if su.StringUtils.trim(ui_lang.lower()) == 'cny' or ui_lang == '1':
                ui_lang = 'cn'
                break
            elif su.StringUtils.trim(ui_lang.lower()) == 'thb' or ui_lang == '2':
                ui_lang = 'th'
                break
            elif ui_lang == 'm':
                ui_lang = None
                break
            else:
                print('Invalid choice [' + ui_lang + ']')
        return ui_lang

    @staticmethod
    def get_user_input_brand():
        ui_brand = None
        while True:
            print('Pick Brand:')
            print('  1: Betway')
            print('  2: Fun88')
            print('  3: TLC')
            print('  4: TBet')
            print('  m: Back to Main Menu')
            print('                ')
            ui_brand = input('Enter Brand: ')
            if su.StringUtils.trim(ui_brand.lower()) == 'betway' or ui_brand == '1':
                ui_brand = 'betway'
                break
            elif su.StringUtils.trim(ui_brand.lower()) == 'fun88' or ui_brand == '2':
                ui_brand = 'fun88'
                break
            elif su.StringUtils.trim(ui_brand.lower()) == 'tlc' or ui_brand == '3':
                ui_brand = 'tlc'
                break
            elif su.StringUtils.trim(ui_brand.lower()) == 'tbet' or ui_brand == '4':
                ui_brand = 'tbet'
                break
            elif ui_brand == 'm':
                ui_brand = None
                break
            else:
                print('Invalid choice [' + ui_brand + ']')
        return ui_brand

    @staticmethod
    def get_user_date(str):
        ui_date = None
        while True:
            ui_date = input(str)
            m = re.search(pattern='[0-9]{4}-[01][0-9]-[0123][0-9]', string=ui_date)
            if m:
                break
            else:
                print('Invalid format for date (YYYY-MM-DD) [' + ui_date + ']')
        return ui_date

    @staticmethod
    def get_user_input_account(
            db_profile,
            param_name
    ):
        # Get all available accounts from DB
        ac_obj = ac.Account(db_profile = db_profile)
        df_accounts = ac_obj.get()
        if type(df_accounts) is list:
            df_accounts = pd.DataFrame(df_accounts)
        else:
            raise Exception('Return value of accounts is not a list!')

        df_accounts = df_accounts.rename(columns={
            ac.Account.COL_ACCOUNT_NAME: CommandLine.DF_COL_NAME,
            ac.Account.COL_ACCOUNT_ID: CommandLine.DF_COL_ID
        })

        # We will return the account ID if successful
        return CommandLine.get_id(df=df_accounts, param_name=param_name)

    @staticmethod
    def get_user_input_campaign(
            db_profile,
            param_name,
            accountId = None
    ):
        # Get all available accounts from DB
        db_obj = cp.Campaign(db_profile = db_profile)
        df_campaigns = db_obj.get(accountId=accountId)
        if type(df_campaigns) is list:
            df_campaigns = pd.DataFrame(df_campaigns)
        else:
            raise Exception('Return value of campaigns is not a list!')

        df_campaigns = df_campaigns.rename(columns={
            cp.Campaign.COL_CAMPAIGN_NAME: CommandLine.DF_COL_NAME,
            cp.Campaign.COL_CAMPAIGN_ID: CommandLine.DF_COL_ID
        })

        # We will return the campaign ID if successful
        return CommandLine.get_id(df=df_campaigns, param_name=param_name)

    @staticmethod
    def get_user_input_bot(
            db_profile,
            param_name,
            account_id = None
    ):
        # Get all available accounts from DB
        db_obj = bt.Bot(db_profile = db_profile)
        df_bots = db_obj.get(accountId=account_id)
        if type(df_bots) is list:
            df_bots = pd.DataFrame(df_bots)
        elif len(df_bots) == 0:
            raise Exception('No bots found for account ID ' + str(account_id) + '!!')
        else:
            raise Exception('Return value of bots is not a list!')

        df_bots = df_bots.rename(columns={
            bt.Bot.COL_BOT_NAME: CommandLine.DF_COL_NAME,
            bt.Bot.COL_BOT_ID: CommandLine.DF_COL_ID,
            bt.Bot.COL_BOT_LANGUAGE: CommandLine.DF_COL_LANG
        })

        # We will return the bot ID if successful
        return CommandLine.get_id(df=df_bots, param_name=param_name)

    @staticmethod
    def get_id(
            # Data Frame containing 2 required columns 'name' & 'id'
            df,
            param_name
    ):
        [id_ret, name_ret, lang_ret] = [None, None, None]

        if df.shape[0] == 0:
            raise Exception('No ' + param_name + '(s) found in DB!')

        while True:
            print('Pick ' + param_name + ':')
            # Form the menu of choices
            for i in range(0, df.shape[0], 1):
                name = df[CommandLine.DF_COL_NAME].loc[i]
                id = df[CommandLine.DF_COL_ID].loc[i]
                print('  ' + str(i+1) + '. ' + name + ' (Id=' + str(id) + ')')
            print('  m: Back to Main Menu')
            print('                ')
            inp = input('Enter ' + param_name + ': ')

            found = False
            for i in range(0, df.shape[0], 1):
                accname = str(df[CommandLine.DF_COL_NAME].loc[i]).lower()
                if su.StringUtils.trim(inp.lower()) == accname or inp == str(i+1):
                    # We will return the account ID
                    id_ret = df[CommandLine.DF_COL_ID].loc[i]
                    name_ret = df[CommandLine.DF_COL_NAME].loc[i]
                    if CommandLine.DF_COL_LANG in df.columns.tolist():
                        lang_ret = df[CommandLine.DF_COL_LANG].loc[i]
                    found = True
                    break

            if found:
                break

            if inp == 'm':
                id_ret = None
                break
            else:
                print('Invalid choice [' + inp + ']')
                id_ret = None
                break

        return [id_ret, name_ret, lang_ret]