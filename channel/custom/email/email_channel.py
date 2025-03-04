import threading

from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel

from common.log import logger
from common.singleton import singleton
from common.tmp_dir import TmpDir
from config import conf, save_config
from .client import EmailchatClient

# from voice.audio_convert import mp3_to_silk
import uuid

MAX_UTF8_LEN = 2048


@singleton
class EmailChatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()

        self.username = conf().get("email_username")
        if not self.username:
            logger.error("[emailchat] username is not set")
            return
        password = conf().get("email_password")
        smtp_server = conf().get("smtp_server")
        smtp_port = conf().get("smtp_port")
        imap_server = conf().get("imap_server")
        imap_port = conf().get("imap_port")
        self.client = EmailchatClient(self.username, password, smtp_server, smtp_port, imap_server, imap_port)
        self.client.login()

        # logger.info(f"[emailchat] init: base_url: {self.base_url}, token: {self.token}, app_id: {self.app_id}, download_url: {self.download_url}")

    def startup(self):
        # 如果app_id为空或登录后获取到新的app_id，保存配置
        fetch_unread_mail_thread = threading.Thread(target=self.client.get_unread_msg, args=(self._compose_context, self.produce), daemon=True)
        fetch_unread_mail_thread.start()

        # 如果原来的self.app_id为空或登录后获取到新的app_id，保存配置

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type == ReplyType.TEXT:
            reply_text = reply.content
            self.client.send_msg(receiver, "Reply", reply_text)
