import random
import threading
from typing import Dict

from .dto import Message, Notification
from .events import Events
from .langChainMA import LangchainMemberAgent, convert_to_langchain_messages
from langchain_core.messages import HumanMessage


class BaseChatManager(LangchainMemberAgent):
    def __init__(self, name, member_id):
        super().__init__(name, member_id)

    def choose_next_speaker(self, chat_id: str, member_id: str):
        self.socket.emit(Events.NEXT_SPEAKER,
                         {'chat_id': chat_id, 'member_id': member_id, 'manager_id': self.member_id})
        
    def produce_notification(self, chat_id: str, to_chat_id: str, notification: str):
        message = self.produce_message(notification, chat_id)
        return Notification(**message.model_dump(), to_chat_id=to_chat_id)
        
    def send_notification_to_chat(self, chat_id: str, to_chat_id: str, notification: str):
        notification = self.produce_notification(chat_id, to_chat_id, notification)
        return self.socket.call(Events.SEND_NOTIFICATION_TO_CHAT, notification.model_dump())
        
    def register_chat_manager(self, chat_id: str):
        ret = self.socket.call(Events.REGISTER_CHAT_MANAGER, {'chat_id': chat_id})
        if not ret['status'] == 'success':
            print('register chat manager failed:', ret)
        else:
            print('register chat manager success:', ret['message'])

    def _on_receive_notification_from_chat(self, notification: Dict):
        threading.Thread(target=self.on_receive_notification_from_chat, args=(Notification(**notification),)).start()
        return True

    def on_receive_notification_from_chat(self, notification: Notification):
        """处理接收到的通知"""
        print(f'{self.name} receive notification from chat:', notification.chat_id)
        from_chat_id = notification.chat_id
        to_chat_id = notification.to_chat_id
        chat_info = self.get_chat(from_chat_id)
        self.send_message(f'来自 {chat_info.name}的通知: {notification.message}', to_chat_id)

    def connect_events(self):
        super().connect_events()
        self.socket.on(Events.RECEIVE_NOTIFICATION_FROM_CHAT, self._on_receive_notification_from_chat)


class ChatManager(BaseChatManager):
    def __init__(self, name: str, member_id: str):
        super().__init__(name, member_id)

        self.choose_next_speaker_method = 'round_robin'

    def get_member_names(self, chat_id: str):
        members = self.get_chat_members(chat_id, need_complete_info=True)
        return [member.name for member in members]

    def get_prompt(self, message: Message):
        chat_id = message.chat_id
        member_names = self.get_member_names(chat_id)
        member_names.remove(self.name)
        last_speaker = message.from_member_name
        member_names.remove(last_speaker)
        # print('choose from member_names:', member_names)

        messages = convert_to_langchain_messages(self.memory.chats[chat_id])
        messages = [message.content for message in messages]
        # 每行代表一个消息
        messages = '\n'.join(messages)

        template = f"""
        {messages}
        Read the above conversation. Then select the next role from {member_names} to play. Only return the role.
        """
        # print('template:', template)
        return template

    def on_receive_message(self, message: Message):
        super().on_receive_message(message)
        next_speaker = self.get_next_speaker(message)
        # print('next speaker:', next_speaker)
        if next_speaker:
            self.choose_next_speaker(message.chat_id, next_speaker)

    def get_next_speaker(self, message: Message):
        chat = self.get_chat(message.chat_id)
        members = chat.members

        # 如果排除manager，只有两个
        members = [member for member in members if member != self.member_id]
        if len(members) == 2:
            message_from = message.from_member_id
            next_speaker = members[0] if message_from == members[1] else members[1]
            # print('next_speaker:', next_speaker)
            return next_speaker
        else:
            # print('超过两个，需要选择')
            if self.choose_next_speaker_method == 'ai':
                return self.get_next_speaker_by_ai(message)
            elif self.choose_next_speaker_method == 'random':
                return self.get_next_speaker_by_random(message)
            elif self.choose_next_speaker_method == 'round_robin':
                return self.get_next_speaker_by_round_robin(message)

    def get_next_speaker_by_ai(self, message: Message):
        prompt = self.get_prompt(message)

        # ret = self.agent.invoke({"messages": [HumanMessage(prompt)]})
        ret = self.model.invoke([HumanMessage(prompt)])

        member_name = ret.content
        print('ai choose ret:', ret)
        member_id = self.get_member_by_name(member_name, message.chat_id).member_id

        print('ai next member name:', member_name)
        if member_id:
            return member_id
        else:
            print('member_id not found')
            return None

    def get_next_speaker_by_random(self, message: Message):
        chat = self.get_chat(message.chat_id)
        members = chat.members
        # 排除manager和上一位发言者
        members = [member for member in members if member != self.member_id and member != message.from_member_id]
        return random.choice(members)

    def get_next_speaker_by_round_robin(self, message: Message):
        chat = self.get_chat(message.chat_id)
        members = chat.members
        members = [member for member in members if member != self.member_id]
        # print('members:', members)
        last_speaker = message.from_member_id
        index = members.index(last_speaker)
        if index == len(members) - 1:
            next_index = 0
        else:
            next_index = index + 1

        member_id = members[next_index]
        member_name = self.get_member(member_id).name
        # print('next speaker:', member_name)
        return members[next_index]


if __name__ == '__main__':
    chat_manager = ChatManager('chat manager', 'chat_manager')
    # chat_manager.signup()
    chat_manager.login()
    chat_manager.socket.wait()
