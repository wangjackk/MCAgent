from typing import List, Dict
from .dto import Message, ReplyData
from .events import Events
from .memberClient import MemberClient
from .memory import AgentChat, AgentChats


# 带有聊天记录的成员客户端
class MemberClientWithChats(MemberClient):
    def __init__(self, name, member_id):
        super().__init__(name, member_id)
        self.memory = AgentChats(member_id=self.member_id)
        # 每个聊天可以有多个参考聊天
        self.reference_chats: Dict[str, List[str]] = {}

    def on_receive_message(self, message: Message):
        # print(f'{self.name}: receive message:{message}')
        self.memory.add_message(message)

    def send_message(self, message: str, chat_id: str) -> Message:
        # 先调用父类的 send_message 生成并发送消息
        message_obj: Message = super().send_message(message, chat_id)
        # 将消息对象添加到内存中
        self.memory.add_message(message_obj)
        return message_obj

    def clear_chat(self, chat_id: str):
        self.memory.clear_chat(chat_id)

    def remove_message(self, message_id: str, chat_id: str) -> bool:
        return self.memory.remove_message(message_id, chat_id)

    def add_reference_chat(self, main_chat_id: str, reference_chat_id: str):
        """添加参考聊天
        
        Args:
            main_chat_id: 主聊天ID
            reference_chat_id: 参考聊天ID
        """
        if main_chat_id not in self.reference_chats:
            self.reference_chats[main_chat_id] = []
        if reference_chat_id not in self.reference_chats[main_chat_id]:
            self.reference_chats[main_chat_id].append(reference_chat_id)

    def remove_reference_chat(self, main_chat_id: str, reference_chat_id: str):
        """移除参考聊天
        
        Args:
            main_chat_id: 主聊天ID
            reference_chat_id: 参考聊天ID
        """
        if main_chat_id in self.reference_chats:
            if reference_chat_id in self.reference_chats[main_chat_id]:
                self.reference_chats[main_chat_id].remove(reference_chat_id)

    def get_all_messages(self, main_chat_id: str) -> List[Message]:
        """获取主聊天及其所有参考聊天的消息
        
        Args:
            main_chat_id: 主聊天ID
            
        Returns:
            所有消息列表，按时间戳排序
        """
        all_messages = []

        # 获取主聊天消息
        main_chat = self.memory.get_chat(main_chat_id)
        if main_chat:
            all_messages.extend(main_chat.messages)

        # 获取参考聊天消息
        if main_chat_id in self.reference_chats:
            for ref_chat_id in self.reference_chats[main_chat_id]:
                ref_chat = self.memory.get_chat(ref_chat_id)
                if ref_chat:
                    all_messages.extend(ref_chat.messages)

        # 按时间戳排序
        return sorted(all_messages, key=lambda x: x.timestamp)


class BaseMemberAgent(MemberClientWithChats):
    def __init__(self, name: str, member_id: str):
        super().__init__(name, member_id)
        self.prompt = None

    def connect_events(self):
        super().connect_events()
        self.socket.on(Events.NEXT_SPEAKER, self._reply)

    def _reply(self, data: dict):
        # print('reply:', data)
        self.reply(ReplyData(**data))

    def reply(self, data: ReplyData):
        """根据主聊天和参考聊天生成回复
        
        Args:
            data: 包含聊天ID的数据对象
        """
        chat_id = data.chat_id
        if chat_id not in self.memory.chats:
            print(f'{self.name}: chat not in chats')
            return

        # 获取所有相关消息
        messages = self.get_all_messages(chat_id)

        # 创建临时聊天对象用于生成回复
        temp_chat = AgentChat(
            chat_id='temp',
            member_id=self.member_id,
            messages=messages
        )
        # chat_info = self.get_chat(chat_id)
        # 打印messages
        # print_messages = ''.join([f'{m.from_member_name}: {m.message}\n' for m in messages])
        # print(f'所在chat:{chat_info.name}, {self.name}的上下文:\n {"<" * 20}\n{print_messages}\n {">" * 20}\n')
        # print(f'所在chat:{chat_info.name}, {self.name}的prompt:\n {"<" * 20}\n{self.prompt}\n {">" * 20}\n')
        # 生成回复
        rsp = self.get_ai_response(self.prompt, temp_chat)
        self.send_message(rsp, chat_id)

    def get_ai_response(self, prompt: str, chat: AgentChat) -> str:
        pass
