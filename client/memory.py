from typing import Dict, List
from pydantic import BaseModel
import os

from .dto import Message


class AgentChat(BaseModel):
    chat_id: str
    messages: List[Message] = []
    member_id: str

    def add_message(self, message: Message):
        self.messages.append(message)

    def clear_messages(self):
        self.messages.clear()

    def remove_message(self, message_id: str):
        self.messages = [message for message in self.messages if message.message_id != message_id]

    def save_to_txt(self, directory: str = "chat_logs"):
        """将聊天消息保存到文本文件
        
        Args:
            directory: 保存文件的目录，默认为 'chat_logs'
        """
        # 确保目录存在
        os.makedirs(directory, exist_ok=True)
        
        # 构建文件路径
        file_path = os.path.join(directory, f"{self.chat_id}.txt")
        
        # 写入消息
        with open(file_path, "w", encoding="utf-8") as f:
            for message in self.messages:
                f.write(f"[{message.timestamp}] {message.from_member_name}: {message.message}\n")


class AgentChats(BaseModel):
    member_id: str
    chats: Dict[str, AgentChat] = {}
    # 存储聊天引用关系
    reference_chats: Dict[str, List[str]] = {}

    def add_message(self, message: Message):
        if message.chat_id not in self.chats:
            self.chats[message.chat_id] = AgentChat(chat_id=message.chat_id, member_id=self.member_id)
        self.chats[message.chat_id].add_message(message)

    def clear_chat(self, chat_id: str):
        if chat_id in self.chats:
            self.chats[chat_id].clear_messages()

    def get_chat(self, chat_id: str) -> AgentChat:
        chat = self.chats.get(chat_id)
        if chat is None:
            chat = self.create_chat(chat_id)
        return chat

    def get_messages(self, chat_id: str) -> List[Message]:
        chat = self.get_chat(chat_id)
        return chat.messages

    def remove_message(self, message_id: str, chat_id: str) -> bool:
        chat = self.chats.get(chat_id)
        if chat:
            chat.remove_message(message_id)
            return True
        return False

    def create_chat(self, chat_id: str) -> AgentChat:
        chat = AgentChat(chat_id=chat_id, member_id=self.member_id)
        self.chats[chat_id] = chat
        return chat

    def add_reference_chat(self, chat_id: str, reference_chat_id: str):
        """添加聊天引用关系
        
        Args:
            chat_id: 主聊天ID
            reference_chat_id: 引用聊天ID
        """
        if chat_id not in self.reference_chats:
            self.reference_chats[chat_id] = []
        if reference_chat_id not in self.reference_chats[chat_id]:
            self.reference_chats[chat_id].append(reference_chat_id)

    def get_reference_chats(self, chat_id: str) -> List[str]:
        """获取指定聊天的所有引用聊天ID
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            List[str]: 引用聊天ID列表
        """
        return self.reference_chats.get(chat_id, [])
