import threading
import time
import uuid
from datetime import datetime
from typing import List, Union, Dict, Callable, Any, Tuple

import requests
import socketio

from .dto import Message, Command, CommandResult, Member, Chat
from .events import Events


def command(name: str = None):
    def decorator(func):
        # 如果没有提供命令名，则使用函数名作为命令名
        func._command_name = name if name else func.__name__
        return func

    return decorator


class MemberClient:
    def __init__(self, name, member_id, description='', url='http://localhost:3000'):
        self.name = name
        self.member_id = member_id
        self.description = description
        self.socket = socketio.Client()
        self.base_url = url

        self.login_success = False  # login状态标识
        self.events_bound = False  # 标识事件是否已经绑定

        self.connect_timeout = 10  # 设置连接超时时间，单位为秒
        self.connection_start_time = None  # 记录连接开始时间

        self.command_handlers: Dict[str, Callable[[Any], str]] = {}
        self.register_commands()

        self.local_chat_members: Dict[str, List[Member]] = {}

    def register_commands(self):
        # 自动注册被 @command 装饰的实例方法
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_command_name'):
                command_name = attr._command_name
                self.command_handlers[command_name] = attr

    def send_command(self, command: str, to: List[str], data: dict = None) -> List[CommandResult]:
        """发送命令并处理可能的超时和错误
        
        Args:
            command: 命令名称
            to: 接收命令的成员列表
            data: 命令数据
            
        Returns:
            List[CommandResult]: 命令执行结果列表
        """
        # 禁止发送空命令
        if command is None or command == '':
            print(f'{self.name} 发送命令失败，命令为空')
            return []
        # 禁止发送空to
        if to is None or len(to) == 0:
            print(f'{self.name} 发送命令失败，to为空')
            return []

        if data is None:
            data = {}
        command_obj = Command(command=command, to=to, data=data, by=self.member_id)
        max_retries = 2
        current_retry = 0

        while current_retry < max_retries:
            try:
                response = self.socket.call(
                    Events.SEND_COMMAND,
                    command_obj.model_dump(),
                    timeout=30  # 设置合理的超时时间
                )
                # print('response:', response)
                return [CommandResult(**r) for r in response]
            except Exception as e:
                print(f"发送命令时发生错误: {str(e)}")
                return []

    def on_receive_command(self, command: dict):
        # 将传入的 dict 数据转为 Command 对象
        command = Command(**command)
        # print(f'{self.name} receive f{_command}')
        handler = self.command_handlers.get(command.command)
        if handler:
            ret = handler(command.data)
            if ret is None:
                ret = ''
            return ret
        else:
            print(f"{self.name} 收到未知命令：{command.command}")
            return f'unknown command,{command.command}'

    def connect_events(self):
        self.events_bound = True  # 确保事件处理程序只绑定一次  
        self.socket.on(Events.RECEIVE_LOGIN_RESPONSE, self.on_receive_login_response)
        self.socket.on(Events.DISCONNECT, self.logout)
        self.socket.on(Events.RECEIVE_MESSAGE, self._on_receive_message)
        self.socket.on(Events.RECEIVE_COMMAND, self.on_receive_command)

    def login(self):
        """连接到 Socket.IO 服务器并传递认证信息"""
        if not self.login_success or not self.socket.connected:
            self.connection_start_time = time.time()
            self.socket.connect(self.base_url, transports=['websocket'],
                                auth={'member_name': self.name, 'member_id': self.member_id})

            # 绑定事件
            if not self.events_bound:
                self.connect_events()

            # 等待登录响应
            while True:
                time.sleep(0.1)  # 等待一段时间，避免占用过多 CPU
                if time.time() - self.connection_start_time > self.connect_timeout:
                    print("Connection timed out. Please try again.")
                    return False
                # print('正在等待login response...')
                if self.login_success:
                    break
        return True

    def on_receive_login_response(self, data):
        """处理登录响应"""
        print('login response:', data)
        if data['status'] == 200:
            print(f"Login Success: {data['message']}")
            self.login_success = True
            self.on_login_success()
        else:
            print(f"Login Failed: {data['message']}")
            self.login_success = False

    def on_login_success(self):
        pass

    def logout(self):
        """断开连接"""
        # self.socket.disconnect()
        self.login_success = False
        print(f"Socketio Disconnected, {self.name} {self.member_id}")

    def produce_message(self, message: str, chat_id: str, message_type: str = 'text') -> Message:
        # print('参数:', message, chat_id, message_type)
        return Message(message=message,
                       message_type=message_type,
                       chat_id=chat_id,
                       from_member_id=self.member_id,
                       from_member_name=self.name,
                       timestamp=str(datetime.now()),
                       message_id=str(uuid.uuid4()),
                       )

    def send_message(self, message: str, chat_id: str) -> Message:
        # 打印发送者的名字和消息内容
        print(f'{datetime.now()} {self.name}:', message)

        # 生成消息对象
        message: Message = self.produce_message(message, chat_id)
        # print('message 对象:', message, type(message))
        try:
            # 使用 sio.call 发送消息并等待服务器响应
            self.socket.call(Events.SEND_MESSAGE, message.model_dump())
            # print('response:', response)
            # 根据服务器返回的响应进行处理
            # if response.get('status') == 'success':
            #     # 消息发送成功的逻辑
            #     pass
            # else:
            #     # 消息发送失败的逻辑，您可以根据需要进行处理
            #     print("消息发送失败:", response.get('message'))
        except TimeoutError:
            print("请求超时，服务器未在指定时间内响应")
        except Exception as e:
            print(f"发生未知错误: {e}")

        return message

    def signup(self) -> dict:
        # 构建请求数据
        data = {
            "member_id": self.member_id,
            "member_name": self.name,
            "description": self.description
        }

        # 发送 POST 请求到 NestJS 后端的 signup 接口
        try:
            print('signup:', self.base_url)
            response = requests.post(self.base_url + '/chat/signup', json=data)
            rsp = response.json()
            response.status_code = rsp['status']
            if response.status_code in [200, 201]:
                print("Signup Success:", response.json())

            else:
                print(f"Signup Failed: {response.status_code} - {response.text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error occurred during signup: {e}")
            return {}

    def _on_receive_message(self, message: Dict):
        threading.Thread(target=self.on_receive_message, args=(Message(**message),)).start()
        return True

    def on_receive_message(self, message: Message):
        """处理接收到的消息"""
        print(f'{self.name} receive_message:', message)

    def get_online_members(self):
        return self.socket.call(Events.GET_ONLINE_MEMBERS)

    def get_chat_online_members(self, chat_id: str):
        return self.socket.call(Events.GET_CHAT_ONLINE_MEMBERS, {'chat_id': chat_id})

    def create_chat(self, name: str, description: str = None, join: bool = True,
                    is_group: bool = True) -> Tuple[bool, Union[Chat, str]]:
        """
        name: 聊天室名称
        description: 聊天室描述
        is_group: 是否为群聊
        """
        try:
            data = {
                'name': name,
                'description': description,
                'is_group': is_group
            }

            response = self.socket.call(Events.CREATE_CHAT, data)
            if response.get('status') == 'success':
                chat_id = response['data']['chat_id']
                print(f"聊天室 {chat_id} 创建成功")
                if join:
                    self.join_chat(chat_id)
                return True, Chat(**response.get('data'))
            else:
                print(f"创建聊天室失败: {response.get('message')}")
                return False, response.get('message')
        except Exception as e:
            print(f"创建聊天室时发生错误: {str(e)}")
            return False, f'发生异常: {str(e)}'

    def join_chat(self, chat_id: str) -> tuple[bool, Any]:
        """
        chat_id: 聊天室ID
        """
        try:
            data = {
                'chat_id': chat_id,
            }
            response = self.socket.call(Events.JOIN_CHAT, data)
            if response.get('status') == 'success':
                print(f"{self.name}成功加入聊天室 {chat_id}")
                return True, response
            else:
                print(f"加入聊天室失败: {response.get('message')}")
                return False, response
        except Exception as e:
            error_msg = f"加入聊天室时发生错误: {str(e)}"
            print(error_msg)
            return False, error_msg

    def get_joined_chats(self) -> List[str]:
        return self.socket.call(Events.GET_JOINED_CHATS)

    def get_chat(self, chat_id: str) -> Chat | None:
        data = {
            'chat_id': chat_id
        }
        response = self.socket.call(Events.GET_CHAT, data)
        if response.get('status') == 'success':
            return Chat(**response.get('data'))
        else:
            return None

    def delete_chat(self, chat_id: str) -> dict:
        data = {
            'chat_id': chat_id
        }
        return self.socket.call(Events.DELETE_CHAT, data)

    def exit_chat(self, chat_id: str) -> dict:
        data = {
            'chat_id': chat_id
        }
        return self.socket.call(Events.EXIT_CHAT, data)

    def pull_members_into_chat(self, chat_id: str, member_ids: List[str]) -> dict:
        data = {
            'chat_id': chat_id,
            'members': member_ids
        }
        return self.socket.call(Events.PULL_MEMBERS_INTO_CHAT, data)

    def get_member(self, member_id: str) -> Member:
        data = {
            'member_id': member_id
        }
        member = self.socket.call(Events.GET_MEMBER, data)
        return Member(**member)

    def get_members(self, member_ids: List[str]) -> List[Member]:
        data = {
            'members': member_ids
        }
        return [Member(**member) for member in self.socket.call(Events.GET_MEMBERS, data)]

    def get_chat_members(self, chat_id: str, need_complete_info: bool = False, try_get_from_local: bool = False) -> \
            List[
                Member | str]:
        if try_get_from_local:
            if chat_id not in self.local_chat_members:
                self.local_chat_members[chat_id] = self.get_chat_members(chat_id, True, False)
            return self.local_chat_members[chat_id]
        data = {
            'chat_id': chat_id,
            'complete': need_complete_info
        }
        members = self.socket.call(Events.GET_CHAT_MEMBERS, data)
        return [Member(**member) if need_complete_info else member for member in members]

    def get_created_chats(self) -> List[Chat]:
        chats = self.socket.call(Events.GET_CREATED_CHATS)
        return [Chat(**chat) for chat in chats]

    def get_member_by_name(self, name: str, chat_id: str, try_get_from_local: bool = True) -> Member:
        if try_get_from_local:
            if chat_id not in self.local_chat_members:
                self.local_chat_members[chat_id] = self.get_chat_members(chat_id, True)
            for member in self.local_chat_members[chat_id]:
                if member.name == name:
                    return member
        data = {
            'name': name,
            'chat_id': chat_id
        }
        member = self.socket.call(Events.GET_MEMBER_BY_NAME, data)
        return Member(**member)

    def remove_member_from_chat(self, chat_id: str, member_id: str):
        data = {
            'chat_id': chat_id,
            'member_id': member_id
        }
        return self.socket.call(Events.REMOVE_MEMBER_FROM_CHAT, data)

    def load_chat_messages_from_server(self, chat_id: str, count: int = -1):
        """
        count: 加载的聊天记录数量，-1表示加载所有
        """
        data = {
            'chat_id': chat_id,
            'count': count
        }
        messages_data = self.socket.call(Events.LOAD_CHAT_MESSAGES_FROM_SERVER, data)
        messages = [Message(**message) for message in messages_data]
        return messages
    
    def listen_in_chat(self, chat_id: str):
        data = {
            'chat_id': chat_id
        }
        return self.socket.call(Events.LISTEN_IN_CHAT, data)
    
    def unlisten_in_chat(self, chat_id: str):
        data = {
            'chat_id': chat_id
        }
        # print('socket connect:', self.socket.connected)
        return self.socket.call(Events.UNLISTEN_IN_CHAT, data)
    
    def get_listen_in_chats(self):
        return self.socket.call(Events.GET_LISTEN_IN_CHATS)

    @command()
    def test(self, data: dict):
        print(f'{self.name} run test command:', data)
        return f'{self.name} this is a test command result'


if __name__ == '__main__':
    ms = []
    for i in range(10):
        member = MemberClient(f"member{i}", f"member_id{i}")
        member.signup()
        success = member.login()
        if success:
            print(f"{member.name} 已连接")
        ms.append(member)
    # ms[0].join_chat('0017f743-a2d2-44d4-9717-1e8b3ba8f9ab')
    # ms[1].join_chat('97e948da-7771-4e3d-9544-c7af23fa1a75')
    # ms[0].send_message("hello from client", "chat_id")
    # ms[0].signup()
    ms[0].socket.wait()
