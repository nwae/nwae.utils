
import mozg.common.data.Account as dbacc
import mozg.common.data.Bot as dbbot
import mozg.common.data.Campaign as dbcp
import mozg.common.data.security.Auth as au
import mozg.common.util.Log as lg
from inspect import currentframe, getframeinfo


class Db:

    def __init__(self):
        return

    @staticmethod
    def get_all_account_id(
            db_profile
    ):
        acc_db = dbacc.Account(
            db_profile = db_profile
        )
        accs = acc_db.get()
        return accs


    @staticmethod
    def get_account_id_from_name(
            account_name,
            db_profile,
            verbose = 0
    ):
        account_id = None

        acc_db = dbacc.Account(
            db_profile = db_profile,
            verbose    = verbose
        )
        accs = acc_db.get(accountName=account_name)

        if type(accs) is list:
            if len(accs) > 1:
                errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': Found more than 1 accounts with name ' + account_name + '! ' + str(accs)
                lg.Log.critical(errmsg)
                raise Exception(errmsg)
            elif len(accs) == 0:
                errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': No accounts with name ' + account_name + '!'
                lg.Log.critical(errmsg)
                raise Exception(errmsg)
            else:
                account_id = int(accs[0][dbacc.Account.COL_ACCOUNT_ID])
        else:
            errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': DB Error, accounts returned non-list!'
            lg.Log.critical(errmsg)
            raise Exception(errmsg)

        return account_id

    @staticmethod
    def get_campaign_id_from_name(
            campaign_name,
            account_id,
            db_profile
    ):
        campaign_id = None

        camp_db = dbcp.Campaign(
            db_profile = db_profile
        )
        camp = camp_db.get(campaignName=campaign_name)

        if type(camp) is list:
            if len(camp) > 1:
                errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': Found more than 1 campaigns with name ' + campaign_name + '! ' + str(camp)
                lg.Log.critical(errmsg)
                raise Exception(errmsg)
            elif len(camp) == 0:
                errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': No campaign with name ' + campaign_name + '!'
                lg.Log.critical(errmsg)
                raise Exception(errmsg)
            else:
                campaign_id = int(camp[0][dbcp.Campaign.COL_CAMPAIGN_ID])
        else:
            errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': DB Error, campaigns returned non-list!'
            lg.Log.critical(errmsg)
            raise Exception(errmsg)

        return campaign_id

    @staticmethod
    def get_bots_for_campaign(
            account_id,
            account_name,
            db_profile
    ):
        #
        # Get campaign bots under this account
        #
        campaign_bots = {}

        cp_db = dbcp.Campaign(
            db_profile = db_profile
        )
        camps = cp_db.get(accountId=account_id)

        bot_db = dbbot.Bot(
            db_profile = db_profile
        )

        if type(camps) is list:
            if len(camps) == 0:
                errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': No campaigns for account ' + account_name + '!'
                lg.Log.critical(errmsg)
                raise Exception(errmsg)

            for camp in camps:
                camp_name = camp[dbcp.Campaign.COL_CAMPAIGN_NAME]
                camp_id = camp[dbcp.Campaign.COL_CAMPAIGN_ID]
                bot_id = camp[dbcp.Campaign.COL_BOT_ID]

                # Get bot
                bot = bot_db.get(botId=bot_id)

                lg.Log.info(str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                + ': Getting bot for campaign [' + camp_name + ']...')
                if type(bot) is list:
                    if len(bot) == 1:
                        botname = bot[0][dbbot.Bot.COL_BOT_NAME]

                        lang = dbcp.Campaign.MAP_CAMPAIGN_BRAND_LANG[camp_name]['lang']
                        brand = dbcp.Campaign.MAP_CAMPAIGN_BRAND_LANG[camp_name]['brand']

                        lg.Log.info(str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                    + ': ......Bot [' + botname + '] (lang=' + lang + ', brand=' + brand + ')...')

                        botkey = lang + '.' + brand
                        #self.bots[botkey] = self.get_bot(lang=lang, bot_key=botkey)

                        campaign_bots[camp_name] = {
                            dbcp.Campaign.COL_CAMPAIGN_ID: camp_id,
                            dbcp.Campaign.COL_CAMPAIGN_NAME: camp_name,
                            dbcp.Campaign.COL_BOT_ID: bot_id,
                            dbbot.Bot.COL_BOT_NAME: botname,
                            # For csv file compatibility
                            'lang': lang,
                            'botkey': botkey
                        }
                    else:
                        errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                                 + ': DB Error, for bot id ' + str(bot_id) + ' returned not 1 item, ' + str(bot)
                        lg.Log.critical(errmsg)
                        raise Exception(errmsg)
                else:
                    errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                             + ': DB Error, Bot query returned non list type!'
                    lg.Log.critical(errmsg)
                    raise Exception(errmsg)
        else:
            errmsg = str(Db.__name__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': DB Error, campaigns returned non-list!'
            lg.Log.critical(errmsg)
            raise Exception(errmsg)

        return campaign_bots

    @staticmethod
    def get_bots_for_account_id(
            db_profile,
            account_id
    ):
        db_obj = dbbot.Bot(db_profile = db_profile)
        rows = db_obj.get(accountId=account_id)

        dic_bots = {}
        for bot in rows:
            bot_id = bot[dbbot.Bot.COL_BOT_ID]
            bot_name = bot[dbbot.Bot.COL_BOT_NAME]
            bot_lang = bot[dbbot.Bot.COL_BOT_LANGUAGE]
            # Standardized language
            bot[dbbot.Bot.COL_BOT_LANGUAGE] = dbbot.Bot.get_bot_lang(language=bot_lang)

            dic_bots[bot_id] = bot

        return dic_bots



if __name__ == '__main__':
    au.Auth.init_instances()

    acid = Db.get_account_id_from_name(
        account_name = 'Welton',
        db_profile   = 'mario1',
        verbose      = 2
    )
    print(acid)

    bots_acid = Db.get_bots_for_account_id(
        db_profile = 'mario2',
        account_id = 3
    )
    print(bots_acid)

    all_accs = Db.get_all_account_id(
        db_profile = 'mario2'
    )
    print(all_accs)