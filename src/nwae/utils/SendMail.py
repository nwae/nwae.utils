# -*- coding: utf-8 -*-

import smtplib
import ssl
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe


class SendMail:

    PORT_SSL = 465
    PORT_SMTP = 587
    GMAIL_SMTP = 'smtp.gmail.com'

    @staticmethod
    def prepare_message(
            from_addr,
            to_addrs_list,
            subject,
            text
    ):
        message = """From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (from_addr, ", ".join(to_addrs_list), subject, text)
        return message

    def __init__(
            self,
            mode = 'smtp'
    ):
        self.mode = mode
        self.__init_smtp()
        return

    def __init_smtp(self):
        if self.mode == 'ssl':
            # Create a secure SSL context
            # self.context = ssl.create_default_context()
            self.server = smtplib.SMTP_SSL(
                host = SendMail.GMAIL_SMTP,
                port = SendMail.PORT_SSL,
                # context=self.context
            )
            self.server.ehlo()
        else:
            self.server = smtplib.SMTP(host=SendMail.GMAIL_SMTP, port=SendMail.PORT_SMTP)
            self.server.ehlo()
            self.server.starttls()
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
            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Login for user "' + str(user) + '" successful.'
            )
            self.server.sendmail(
                from_addr = user,
                to_addrs  = recipients_list,
                msg       = message
            )
            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Message from '+ str(user) + ' to ' + str(recipients_list)
                + ' sent successfully.'
            )
            self.server.close()
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': Exception sending mail from ' + str(user) + ' to ' + str(recipients_list)\
                     + '. Got exception ' + str(ex) + '.'
            Log.error(errmsg)
            raise Exception(errmsg)


if __name__ == '__main__':
    user = '?@gmail.com'
    receivers = ('mapktah@ya.ru')
    subject = 'Test mail Python'
    text = 'Test message from Python client'
    message = SendMail.prepare_message(
        from_addr = user,
        to_addrs_list = receivers,
        subject = subject,
        text = text
    )

    # message = """From: From Kim Bon <kimbon@gmail.com>
    # To: To All
    # Subject: SMTP e-mail test
    #
    # This is a test e-mail message.
    # """

    mail = SendMail()
    mail.send(
        user = user,
        password = 'password123',
        recipients_list = receivers,
        message = message
    )
