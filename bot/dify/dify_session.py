from common.expired_dict import ExpiredDict
from common.log import logger
from config import conf


class DifySession(object):
    def __init__(self, session_id, conversation_id=''):
        self.__session_id = session_id
        self.__user = session_id # 直接把session_id作为user
        self.__conversation_id = conversation_id

    def get_session_id(self):
        return self.__session_id

    def get_user(self):
        return self.__user

    def get_conversation_id(self):
        return self.__conversation_id

    def set_conversation_id(self, conversation_id):
        self.__conversation_id = conversation_id


class DifySessionManager(object):
    def __init__(self, sessioncls, **session_kwargs):
        if conf().get("expires_in_seconds"):
            sessions = ExpiredDict(conf().get("expires_in_seconds"))
        else:
            sessions = dict()
        self.sessions = sessions
        self.sessioncls = sessioncls
        self.session_kwargs = session_kwargs

    def _build_session(self, session_id):
        """
        如果session_id不在sessions中，创建一个新的session并添加到sessions中
        """
        if session_id is None:
            return self.sessioncls(session_id)

        if session_id not in self.sessions:
            self.sessions[session_id] = self.sessioncls(session_id)
        session = self.sessions[session_id]
        return session

    def get_session(self, session_id):
        session = self._build_session(session_id)
        return session

    def clear_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def clear_all_session(self):
        self.sessions.clear()
