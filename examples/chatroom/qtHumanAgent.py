from PySide6.QtCore import QObject, Signal

from client.dto import Message, ReplyData
from client.memberAgent import BaseMemberAgent


class QtHumanAgent(BaseMemberAgent, QObject):
    """Qt版本的HumanAgent，添加信号支持"""

    # 定义信号
    message_received = Signal(Message)  # 收到消息信号
    message_sent = Signal(Message)  # 发送消息信号
    login_succeed = Signal()  # 登录成功信号

    def __init__(self, name: str, member_id: str):
        super().__init__(name=name, member_id=member_id)
        QObject.__init__(self)

    def send_message(self, text: str, chat_id: str):
        """重写发送消息方法"""
        # 调用父类方法发送消息
        message = super().send_message(text, chat_id)
        # 发送消息发送信号
        if message:
            self.message_sent.emit(message)
        return message

    def on_receive_message(self, message: Message):
        """重写消息接收方法"""
        # 发送消息接收信号
        self.message_received.emit(message)
        # 调用父类方法处理消息
        super().on_receive_message(message)

    def reply(self, data: ReplyData):
        """重写回复方法"""
        # chat_id = data.chat_id
        print('轮到你发言了')

    def on_login_success(self):
        self.login_succeed.emit()
