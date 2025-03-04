from .api.message_api import MessageApi
from .api.login_api import LoginApi


class EmailchatClient:
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

    def __init__(self, username, password, smtp_server, smtp_port, imap_server, imap_port):
        self.client = LoginApi(username, password, smtp_server, smtp_port, imap_server, imap_port)
        self.message_api = MessageApi(self.client.server)

    # Login API methods
    def login(self):
        """登录"""
        return self.client.login()

    def get_unread_msg(self, _compose_context, product_fuc):
        """获取未读消息"""
        return self.message_api.revices(_compose_context, product_fuc)

    def send_msg(self, to_email, subject, body):
        """发送邮件"""
        from_email = self.client.username
        return self.message_api.post_text(from_email, to_email, subject, body)
