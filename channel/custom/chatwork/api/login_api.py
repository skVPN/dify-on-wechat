from .base_api import Chatwork
from common.log import logger


class LoginApi:
    def __init__(self, api_key):
        self.api_key = api_key
        self.server = None

    def login(self):
        try:
            self.server = Chatwork(self.api_key)
            self.server.get_me()
            logger.info(f"Login success:{self.api_key}")
        except Exception as e:
            logger.error(e)
