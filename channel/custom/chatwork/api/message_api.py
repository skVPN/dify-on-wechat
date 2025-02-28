import time
from common.log import logger

class MessageApi:
    def __init__(self, server):
        self.server = server
        print("server init",self.server)
    def post_text(self, room_id,msg):
        """发送消息"""
        if self.server is None:
            print('Not logged in')
        try:
            if self.server.send_message(room_id,msg):
                logger.info('Email sent successfully')
        except Exception as e:
            logger.exception(f'Failed to send email: {e}')

    def recive(self,parse_fuc):
        """获取新消息"""
         
        while True:
            data_set = self.server.get_rooms()
            if not data_set:
                time.sleep(5)
                continue
            for rooms in data_set[1:]:
                for room in rooms:
                    if room['unread_num']:
                        room_id = room["room_id"]
                        messages = self.server.get_rooms_messages(room_id)
                        if  messages:
                            for message in messages:
                                logger.info(f"recive msg:{message}")
                                message['room_id'] = room_id
                                parse_fuc(message)
            
            time.sleep(5)

                
                
        return "success"