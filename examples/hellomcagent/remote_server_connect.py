from client.chatManager import ChatManager
from client.langChainMA import LangchainMemberAgent

member = LangchainMemberAgent("tom", "wjk_001")
manager = ChatManager("manager", "manager_001")
member.base_url = 'http://121.37.253.121'
manager.base_url = 'http://121.37.253.121'
member.login()
# manager.signup()
manager.login()
member.socket.wait()