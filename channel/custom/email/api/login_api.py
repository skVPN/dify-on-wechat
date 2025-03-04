import smtplib
from common.log import logger
from types import SimpleNamespace
import imaplib


class LoginApi:
    def __init__(self, username, password, smtp_server, smtp_port, imap_server, imap_port):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.username = username
        self.password = password
        self.server = SimpleNamespace()
        self.server.username = username

    def login(self):
        self.server.smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        self.server.smtp.login(self.username, self.password)

        self.server.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        self.server.imap.login(self.username, self.password)
        logger.info(f"Email login : {self.username} Login success with smtp and imap:{self.server.imap}")
