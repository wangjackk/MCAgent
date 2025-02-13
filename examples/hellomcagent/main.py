from client.chatManager import ChatManager
from client.dto import ReplyData
from client.langChainMA import LangchainMemberAgent
from client.memberAgent import BaseMemberAgent


class HumanAgent(BaseMemberAgent):
    def __init__(self, name, member_id):
        super().__init__(name, member_id)

    def reply(self, data: ReplyData):
        chat_id = data.chat_id
        input_text = input('请输入你的发言:')
        self.send_message(input_text, chat_id)


def main():
    # 创建参与者
    human = HumanAgent("Human", "human_001")
    assistant = LangchainMemberAgent("Bot", "ai_001")
    manager = ChatManager("Manager", "manager_001")

    # 注册 一次即可
    # human.signup()
    # assistant.signup()
    # manager.signup()

    # 登录
    human.login()
    assistant.login()
    manager.login()

    # 创建聊天 创建一次即可，之后只需要chat_id
    # _, chat = manager.create_chat(
    #     name="测试聊天",
    #     description="人机对话测试",
    # )
    # chat_id = chat.chat_id
    chat_id = '6adde71f-f30d-442a-8cab-897b8f8365f3'

    # 添加成员，一次即可
    # manager.pull_members_into_chat(chat_id, [human.member_id, assistant.member_id])

    human.send_message("你好", chat_id)
    human.socket.wait()

if __name__ == '__main__':
    main()