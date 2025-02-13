from typing import Optional, List, Any

from pydantic import BaseModel


class Member(BaseModel):
    member_id: str
    name: str
    description: Optional[str] = None
    listen_in_chats: List[str] = []


class Message(BaseModel):
    message: str
    message_type: str
    chat_id: str
    from_member_id: str
    from_member_name: str = ''
    timestamp: str = ''
    message_id: str


class Notification(Message):
    to_chat_id: str


class Chat(BaseModel):
    chat_id: str
    name: str
    description: Optional[str] = None
    is_group: bool
    members: List[str] = []
    messages: List[str] = []
    created_by: str
    createdAt: str
    # 管理员 控制chat中成员发送的顺序
    manager: str = None
    # 监听者 当chat发生消息时，监听者会收到消息，但不会参与聊天
    listeners: List[str] = []



class Command(BaseModel):
    command: str
    by: str
    to: Optional[List[str]] = None  # 指定接收命令的成员列表，现在是可选的
    data: dict = None  # 命令携带的数据


class CommandBasicInfo(BaseModel):
    command: str
    by: str
    to: str


class CommandResult(BaseModel):
    result: Any
    command: CommandBasicInfo


class ReplyData(BaseModel):
    chat_id: str
