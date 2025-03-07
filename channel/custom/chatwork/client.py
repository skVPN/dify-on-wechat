import shelve
import time
import os
from .api.message_api import MessageApi
from .api.login_api import LoginApi
from common.log import logger


class ChatWorkClient:
    """
    GewechatClient 是一个用于与GeWeChat服务进行交互的客户端类。
    它提供了多种方法来执行各种微信相关的操作，如管理联系人、群组、消息等。

    使用示例:
    ```
    # 初始化客户端
    client = GewechatClient("http://服务ip:2531/v2/api", "your_token_here")
    app_id = "your_app_id"
    # 获取联系人列表
    contacts = client.fetch_contacts_list(app_id)

    # 发送文本消息
    client.post_text(app_id, "wxid", "Hello, World!")

    # 获取个人资料
    profile = client.get_profile(app_id)
    ```

    注意: 在使用任何方法之前，请确保你已经正确初始化了客户端，并且有有效的 base_url 和 token。
    """

    def __init__(self, api_key, my_name):
        self.client = LoginApi(api_key)
        self.my_name = my_name
        self.login()
        self.message_api = MessageApi(self.client.server)
        self.name_id_map_file = "name_id_map.json"
        self.init_id_name_map()

    def init_id_name_map(self):
        self.id_name_map = {}
        self.name_id_map = {}

        if not os.path.exists(self.name_id_map_file):
            self.id_name_map = self.get_contacts()
        else:
            with shelve.open(self.name_id_map_file) as shelf:
                self.id_name_map = dict(shelf)
        if self.id_name_map:
            self.name_id_map = dict(zip(self.id_name_map.values(), self.id_name_map.keys()))

    # Login API methods
    def login(self):
        """登录"""
        self.client.login()

    def get_unread_msg(self, parse_fuc):
        """获取未读消息"""
        return self.message_api.recive(parse_fuc)

    def send_msg(self, room_id, msg):
        """发送邮件"""
        return self.message_api.post_text(room_id, msg)

    def send_file(self, room_id, file_path, file_name, message):
        return self.message_api.post_file(room_id, file_path, file_name, message)

    def get_contacts(self):
        """2. 好友id和name的映射关系"""
        # [{'account_id': 10124706, 'room_id': 388277412, 'name': 'chenshi', 'chatwork_id': '', 'organization_id': 7810521, 'organization_name': '', 'department': '', 'avatar_image_url': 'https://appdata.chatwork.com/avatar/ico_default_blue.png'}]
        while 1:
            info = self.message_api.server.get_contacts()
            print("get_contacts info====", info)

            if "errors" in info:  # {'errors': ['Rate limit exceeded']}
                logger.info("接口频率超过限制,稍等")
                time.sleep(10)
                continue
            data = {str(i["account_id"]) if isinstance(i["account_id"], int) else i["account_id"]: i["name"] for i in info}
            print("id_name site", data)
            with shelve.open(self.name_id_map_file) as shelf:
                shelf.update(data)
                ret = dict(shelf)
                return ret

    def get_name_id(self, arg_str):
        """先从本地获取，如果没有则走网络请求"""
        ret = None
        now_get = False
        if isinstance(arg_str, int):
            arg_str = str(arg_str)
        for _ in range(2):

            if arg_str.isdigit():  # id
                ret = self.name_map.get(arg_str)
            else:
                reversed_dict = dict(zip(self.name_map.values(), self.name_map.keys()))
                ret = reversed_dict.get(arg_str)
            if ret:
                break
            if not now_get:  # 刚获取就不用再去获取一次了
                self.name_map = self.get_contacts()
                continue
        return ret

    def name_to_id(self, name_str):
        ret = self.name_id_map.get(name_str)
        if not ret:
            self.init_id_name_map()
            ret = self.name_id_map.get(name_str)
        return ret 
    def id_to_name(self, id_str):
        ret = self.id_name_map.get(id_str)
        if not ret:
            self.init_id_name_map()
            ret = self.id_name_map.get(id_str)
        return ret
    
    def update_name_map(self, id_str, name_str):
        if isinstance(id_str, int):
            id_str = str(id_str)
        self.id_name_map[id_str] = name_str
        with shelve.open(self.name_id_map_file, writeback=True) as shelf:
            shelf[id_str] = name_str
