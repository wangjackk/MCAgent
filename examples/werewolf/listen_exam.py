from dto import Message
from memberClient import MemberClient


class Listener(MemberClient):
    def __init__(self, name: str, member_id: str):
        super().__init__(name, member_id)

    def on_receive_message(self, message: Message):
        print(f'{message.chat_id} : {message.from_member_name} : {message.message}')
        return super().on_receive_message(message)


villagers_chat_id = 'b2acd6d3-4c61-4680-a012-be55bdd92d9b'
wolves_chat_id = '73dc7671-3da1-4a8a-afff-db3b6ed25a8d'
admin = Listener('admin', 'admin001')
success = admin.login()
print(success)
# admin.unlisten_in_chat(villagers_chat_id)
print(admin.load_chat_messages_from_server(villagers_chat_id, 3))
admin.listen_in_chat(villagers_chat_id)
admin.listen_in_chat(wolves_chat_id)
admin.socket.wait()
