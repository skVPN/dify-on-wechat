from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from types import SimpleNamespace

from email import encoders
import time
import email
from email.header import decode_header
from common.log import logger
from bridge.context import ContextType

class MessageApi:
    def __init__(self, server):
        self.server = server

    def post_text(self,  from_email, to_email, subject, body, attachments=None):
        """发送邮件消息"""
        if self.server.smtp is None:
            print('Not logged in')
            return

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if attachments:
            for filename in attachments:
                try:
                    with open(filename, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                        msg.attach(part)
                except Exception as e:
                    print(f'Failed to attach file {filename}: {e}')

        try:
            self.server.smtp.sendmail(from_email, to_email, msg.as_string())
            logger.info('Email sent successfully')
        except Exception as e:
            logger.exception(f'Failed to send email: {e}')

    def revices(self,_compose_context,product_fuc):
        """接收邮件"""
         
        while True:
            time.sleep(1)
            # 4. 搜索未读邮件 (可以根据需要修改搜索条件)
            self.server.imap.select('INBOX')  # 这将切换到选中的邮箱状态
            status, data = self.server.imap.search(None, "UNSEEN")  # 搜索未读邮件
            if status != "OK":
                logger.error("搜索邮件失败")
                self.server.imap.close()
                self.server.imap.logout()
                return

            mail_ids = data[0].split()
            logger.info(f"收件中:{mail_ids}")
            # 5. 获取并解析邮件
            for i,mail_id in enumerate(mail_ids):
                status, data = self.server.imap.fetch(mail_id, "(RFC822)")
                if status != "OK":
                    print(f"获取邮件 {mail_id} 失败")
                    continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                # 6. 解析邮件内容
                # 解码邮件主题
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")
                # 获取发件人
                from_ = msg.get("From")

                print(f"{i}: 主题: {subject}-发件人: {from_}")
                # 解码邮件内容
                # 获取邮件正文
                if msg.is_multipart():
                    for part in msg.walk():
                        content_disposition = str(part.get("Content-Disposition"))

                        if "attachment" not in content_disposition:
                            try:
                                body = part.get_payload(decode=True).decode()
                            except:
                                body = part.get_payload(decode=True)
                            print(f"正文: {body}")
                else:
                    body = msg.get_payload(decode=True).decode()
                  
                content=f"{i}: 主题: {subject}-发件人: {from_},body:{body}"
                msg= SimpleNamespace(from_user_nickname=from_,other_user_nickname=from_,other_user_id=from_,actual_user_id=from_,actual_user_nickname=from_)
                msg.Data ={"MsgType": 1, "Content": {"string": body}}

                context = _compose_context(
                ContextType.TEXT,
                content,
                isgroup=False,
                msg=msg,
                receiver=from_,
                session_id=from_
                )
                product_fuc(context)
                
                
        return "success"