from types import SimpleNamespace
import json
import os
import threading
import re
from bridge.context import ContextType
import time
import tempfile

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
        self.client = ChatWorkClient(self.api_key, self.my_name)
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
        fetch_unread_mail_thread = threading.Thread(target=self.client.get_unread_msg, args=(self.parse_msg,), daemon=True)
        fetch_unread_mail_thread.start()

    def parse_msg(self, origin_msg=None):
        """解析消息
        {'message_id': '1947277194111881216', 'account': {'account_id': 10124706, 'name': 'chenshi', \
            'avatar_image_url': 'https://appdata.chatwork.com/avatar/ico_default_blue.png'},
         'body': '有\n看看', 'send_time': 1740740661, 'update_time': 0}
        """

        room_id = None
        body = None
        msg = None
        context_type = ContextType.TEXT  # default
        account_id = ""
        receiver = ""
        content = ""  # for img path
        if "message_id" in origin_msg:  # 处理消息
            # 如果是回复：{'message_id': '1948626525465219072', 'account': {'account_id': 10124706, 'name': 'chenshi', 'avatar_image_url': 'https://appdata.chatwork.com/avatar/ico_default_blue.png'}, 'body': '[rp aid=10125216 to=388277412-1947558692782219264]William William Thomas\n真的吗', 'send_time': 1741062367, 'update_time': 0}
            # 如果是引用{'message_id': '1948651155563352064', 'account': {'account_id': 10124706, 'name': 'chenshi', 'avatar_image_url': 'https://appdata.chatwork.com/avatar/ico_default_blue.png'}, 'body': '[qt][qtmeta aid=10125216 time=1741068226]嘿嘿，亲爱的客官~我就是您的奶茶小姐姐啦！有什么可爱的需求我可以帮您满足呢？快点告诉我吧，让我来给您调制一杯暖心美味的奶茶吧！嘻嘻~😊💕🍵[/qt]\n胡说', 'send_time': 1741068239, 'update_time': 0}
            # 如果是图片 {'message_id': '1948653001778540544', 'account': {'account_id': 10124706, 'name': 'chenshi', 'avatar_image_url': 'https://appdata.chatwork.com/avatar/ico_default_blue.png'}, 'body': '[info][title][dtext:file_uploaded][/title][preview id=1693905617 ht=111][download:1693905617]image_2025_3_4.png (3.62 KB)[/download][/info]', 'send_time': 1741068679, 'update_time': 0
            from_ = origin_msg["account"]["name"]
            account_id = origin_msg["account"]["account_id"]
            if from_ == self.client.my_name or origin_msg["send_time"] < self.last_msg_time:  # 自己的和过去的不用回复
                return
            body = origin_msg["body"]
            self.last_msg_time = origin_msg["send_time"]
            room_id = origin_msg["room_id"]
            receiver = room_id
            if "file_uploaded" in str(origin_msg):
                tmp_file_path = self.parse_file(room_id, origin_msg)
                body = tmp_file_path
                context_type = ContextType.FILE
                if "image" in str(origin_msg):
                    context_type = ContextType.IMAGE

        elif "request_id" in origin_msg:  # 处理好友申请
            # [{'request_id': 38566451, 'account_id': 10124706, 'message': 'xxx', 'name': 'chenshi', 'chatwork_id': '', 'organization_id': 7810521, 'organization_name': '', 'department': '', 'avatar_image_url': 'https://appdata.chatwork.com/avatar/ico_default_blue.png'}]

            context_type = ContextType.ACCEPT_FRIEND
            room_id = origin_msg["request_id"]
            body = origin_msg["request_id"]
            account_id = origin_msg["account_id"]
            receiver = origin_msg["name"]

        msg = SimpleNamespace(from_user_nickname=from_, other_user_nickname=from_, other_user_id=from_, actual_user_id=from_, actual_user_nickname=from_)
        msg.Data = {"MsgType": 1, "Content": {"string": body}, "account_id": account_id}

        context = self._compose_context(context_type, body, isgroup=False, msg=msg, receiver=receiver, session_id=room_id)
        self.produce(context)

    def parse_file(self, room_id, msg):
        """获取细节的上传图片或者文件，"""
        # {'file_id': 1693930876, 'message_id': '1948656846306938880', 'filesize': 12010, 'filename': 'image_2025_3_4.png', 'upload_time': 1741069583, 'account': {'account_id': 10124706, 'name': 'chenshi', 'avatar_image_url': 'https://appdata.chatwork.com/avatar/ico_default_blue.png'}, 'download_url': 'https://appdata.chatwork.com/uploadfile/388277/388277412/2612148bc8c64e75f75cd68a21c8b14d.dat?response-content-type=&response-content-disposition=attachment%3Bfilename%2A%3DUTF-8%27%27image_2025_3_4.png&Expires=1741069626&Signature=kg5r6CnyV8zNNq~X-GttuqUaKv3WmueA~o-ZWFS5rlw6R7XjwDfx99ZIayCpAvEBkTSp-DNqlZiEGYLBjxsD-nAKp~zGl8c5avjdr9Qzd9vqvNI-wQAHyl2ecTOw77I3y2ZoNawhxvyEXvgYi6E5Y-NOZf~MZUc2yavTbTAfJedAvJxjCLuNaUTjRy3-na0A7WxI0Jc9fEH68LGLXrf~Xht-KHDtzDunvhuJRGppKhmrWhoydysujZ5fAbJlyPQPokr~NVufXq9L-8SVUtYCOx9BWLuzufjVbbmKuLIxxOebvvwDCPI5B11mmd1uK67EP0cq3MhpVVDEKzM4dCXz-g__&Key-Pair-Id=APKAIZEFQUITKUSISS7A'}
        download_id = re.findall("download:(\d+)", str(msg))[0]
        img_name = re.findall("download:.*?\](.*?)\s", str(msg))[0]
        data = self.client.client.server.get_rooms_file_information(room_id, download_id)
        download_url = data["download_url"]
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=img_name) as tmp_file:
            response = self.client.client.server.download_file(download_url)
            tmp_file.write(response.content)
            print(f"临时文件路径: {tmp_file.name}")
            return tmp_file.name

    def send(self, reply: Reply, context: Context):
        room_id = context["receiver"]
        if reply.type == ReplyType.TEXT:
            rely_msg = reply.content
            self.client.send_msg(room_id, rely_msg)
        if reply.type in (ReplyType.IMAGE, ReplyType.VOICE, ReplyType.FILE):
            rely_msg = reply.content
            # self.client.send_file(room_id, file_path, file_name,  message)

    def _build_friend_request_reply(self, context):
        """处理好友申请"""
        print("context", context)
        request_id = context["content"]
        if self.client.client.server.approve_incoming_requests(request_id):
            logger.info(f"好友申请通过,from:{context['receiver']},text:{context['msg']}")
            self.client.update_name_map(context["msg"], context["receiver"])
            time.sleep(3)
