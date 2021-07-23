# -*- coding: utf-8 -*-

from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from nwae.utils.SendMail import SendMail
from datetime import datetime


class EmailAlerts:

    def __init__(
            self,
            from_addr,
            password,
            alert_recipients,
            # Default limit per hour
            limit_per_hour = 8,
            fake_send = False,
            mail_mode = SendMail.MAIL_MODE_SMTP,
            mail_server_url  = SendMail.GMAIL_SMTP,
            mail_server_port = SendMail.PORT_SMTP
    ):
        self.from_addr = from_addr
        self.password = password
        self.alert_recipients = alert_recipients
        self.fake_send = fake_send
        self.mail_mode = mail_mode
        self.mail_server_url = mail_server_url
        self.mail_server_port = mail_server_port

        # Limit to
        self.limit_per_hour = limit_per_hour
        self.current_hour = datetime.now().hour
        self.emails_sent_this_hour = 0
        return

    def set_alert_recipients(self, alert_recipients):
        self.alert_recipients = alert_recipients

    def __send_email(
            self,
            text_subject,
            text_msg,
            files,
            ignore_limit
    ):
        email_msg = SendMail.prepare_message(
            from_addr     = self.from_addr,
            to_addrs_list = self.alert_recipients,
            subject       = text_subject,
            text          = text_msg,
            files         = files
        )
        try:
            # Check how many already sent this hour
            if datetime.now().hour != self.current_hour:
                self.current_hour = datetime.now().hour
                self.emails_sent_this_hour = 0

            if not ignore_limit:
                if self.emails_sent_this_hour >= self.limit_per_hour:
                    Log.warning(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Send email alert limit ' + str(self.limit_per_hour)
                        + ' per hour hit. Not sending subject: "' + str(text_subject)
                        + '", message: ' + str(text_msg)
                    )
                    return
            else:
                Log.info(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Ignoring send limit of ' + str(self.limit_per_hour) + ' per hour.'
                )

            if self.fake_send:
                print(
                    'Fake send email from "' + str(self.from_addr) + '" to: ' + str(self.alert_recipients)
                    + ' Message:\n\r' + str(email_msg)
                )
            else:
                SendMail(
                    mode = self.mail_mode,
                    mail_server_url  = self.mail_server_url,
                    mail_server_port = self.mail_server_port
                ).send(
                    user            = self.from_addr,
                    password        = self.password,
                    recipients_list = self.alert_recipients,
                    message         = email_msg
                )
            self.emails_sent_this_hour += 1
        except Exception as ex_mail:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error sending email: ' + str(ex_mail) + '. Could not send message: '
                + str(email_msg)
            )

    def send_alerts(
            self,
            text_subject,
            text_msg,
            files = None,
            ignore_limit = False
    ):
        self.__send_email(
            text_subject = text_subject,
            text_msg     = text_msg,
            files        = files,
            ignore_limit = ignore_limit
        )
        return


if __name__ == '__main__':
    em_alert = EmailAlerts(
        mail_mode = 'smtp-starttls',
        from_addr = '?@gmail.com',
        password  = 'M@...',
        alert_recipients = ['mapktah@ya.ru'],
        limit_per_hour = 10,
        fake_send = False
    )

    em_alert.send_alerts(
        text_subject = 'Alert XXX',
        text_msg     = 'Test alert XXX',
        files        = ['/tmp/pic1.png', '/tmp/pic2.png']
    )

    em_alert.fake_send = True

    for i in range(20):
        print(i)
        ignore_limit = False
        if i == 18:
            ignore_limit = True
        em_alert.send_alerts(
            text_subject = 'Alert XXX',
            text_msg     = 'Test alert XXX',
            ignore_limit = ignore_limit
        )
    exit(0)
