# -*- coding: utf-8 -*-

import smtplib
import ssl
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe


class SendMail:

    PORT_SSL = 465
    GMAIL_SMTP = 'smtp.gmail.com'

    def __init__(
            self
    ):
        self.__init_ssl()
        return

    def __init_ssl(self):
        # Create a secure SSL context
        self.context = ssl.create_default_context()
        self.server = smtplib.SMTP_SSL(SendMail.GMAIL_SMTP, SendMail.PORT_SSL, context=self.context)
        Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': SMTP SSL successfully initialized.'
        )
        return

    def send(
            self,
            user,
            password,
            recipients_list,
            message
    ):
        try:
            self.server.login(
                user = user,
                password = password
            )
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Login for user "' + str(user) + '" successful.'
            )
            self.server.sendmail(
                from_addr = user,
                to_addrs  = recipients_list,
                msg       = message
            )
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Message from '+ str(user) + ' to ' + str(recipients_list)
                + ' sent successfully.'
            )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception sending mail from ' + str(user) + ' to ' + str(recipients_list)\
                     + '. Got exception ' + str(ex) + '.'
            Log.error(errmsg)
            raise Exception(errmsg)


if __name__ == '__main__':
    user = '705270564@gmail.com'
    receivers = ('705270564@qq.com')

    message = """From: From Kim Bon <kimbon@gmail.com>
    To: To All
    Subject: SMTP e-mail test

    This is a test e-mail message.
    """

    mail = SendMail()
    mail.send(
        user = user,
        password = '',
        recipients_list = receivers,
        message = message
    )
