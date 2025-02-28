from types import SimpleNamespace
import json
import os
import threading
from bridge.context import ContextType
import time
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel

from common.log import logger
from common.singleton import singleton
from common.tmp_dir import TmpDir
from config import conf, save_config
from .client import ChatWorkClient
MAX_UTF8_LEN = 2048


@singleton
class ChatWorkChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.conf = self.load_config()
        self.api_key = self.conf.get("api_key")
        self.my_name = self.conf.get("my_name")
        self.client = ChatWorkClient(self.api_key,self.my_name)
        self.last_msg_time = int(time.time())

    def load_config(self):
        curdir = os.path.dirname(__file__)

        config_path = os.path.join(curdir, "config.json")
        conf = None
        if not os.path.exists(config_path):
            logger.debug(f"[keyword]不存在配置文件{config_path}")
            raise Exception("WorkChatChannel config.json 配置缺失")
        else:
            logger.debug(f"[keyword]加载配置文件{config_path}")
            with open(config_path, "r", encoding="utf-8") as f:
                conf = json.load(f)
            # 加载关键词
        return conf

    def startup(self):
        # 如果app_id为空或登录后获取到新的app_id，保存配置
        fetch_unread_mail_thread = threading.Thread(target=self.client.get_unread_msg,args=(self.parse_msg,),daemon=True)
        fetch_unread_mail_thread.start()

    def parse_msg(self,origin_msg=None):
        """解析消息
        {'message_id': '1947277194111881216', 'account': {'account_id': 10124706, 'name': 'chenshi', \
            'avatar_image_url': 'https://appdata.chatwork.com/avatar/ico_default_blue.png'},
         'body': '有\n看看', 'send_time': 1740740661, 'update_time': 0}
        """
        body=origin_msg['body']
        from_=origin_msg['account']['name']
        if from_ == self.client.my_name or origin_msg['send_time']<self.last_msg_time:  # 自己的和过去的不用回复
            return
        self.last_msg_time = origin_msg['send_time']
        room_id=origin_msg['room_id']
        msg= SimpleNamespace(from_user_nickname=from_,other_user_nickname=from_,other_user_id=from_,actual_user_id=from_,actual_user_nickname=from_)
        msg.Data ={"MsgType": 1, "Content": {"string": body}}

        context = self._compose_context(
        ContextType.TEXT,
        body,
        isgroup=False,
        msg=msg,
        receiver=room_id,
        session_id=room_id
        )
        self.produce(context)

    def send(self, reply: Reply, context: Context):
        room_id = context["receiver"]
        if reply.type==ReplyType.TEXT:
            rely_msg = reply.content
            self.client.send_msg(room_id, rely_msg)