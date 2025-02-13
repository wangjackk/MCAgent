base_url = "https://openrouter.ai/api/v1"
api_key = 'xxx'
model = "google/gemini-2.0-flash-001"

from enum import Enum
from typing import List
from pydantic import BaseModel

from dto import Message
from memberAgent import BaseMemberAgent
from memory import AgentChat


# 定义角色枚举，确保角色只能取固定值
class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"  # 可选，用于函数调用


# 定义消息模型，每条消息包含 role 和 content 两个字段
class OpenAIMessage(BaseModel):
    role: str
    content: str


from openai import OpenAI


# client = OpenAI(
#   base_url="https://openrouter.ai/api/v1",
#   api_key=api_key,
# )

# completion = client.chat.completions.create(
#   model=model,
#   messages=[
#     {
#       "role": "user",
#       "content": "2025世界ai势力介绍"
#     }
#   ]
# )
# mes = OpenAIMessage(role=Role.USER.value, content='2025世界可能发生的大事')
# print(mes.model_dump())
# print(completion.choices[0].message.content)


class OpenRouterLLM:
    def __init__(self, model):
        self.model = model

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    def invoke(self, messages: List[OpenAIMessage]):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[message.model_dump() for message in messages]
        )
        print('ai 回复:', completion)
        return completion.choices[0].message.content


def convert_to_openrouter_messages(agent_chat: AgentChat) -> List[OpenAIMessage]:
    openrouter_messages = []
    for message in agent_chat.messages:
        if message.from_member_id == agent_chat.member_id:
            openrouter_messages.append(OpenAIMessage(role=Role.ASSISTANT.value, content=message.message))

        else:
            openrouter_messages.append(
                OpenAIMessage(role=Role.USER.value, content=f'{message.from_member_name}: {message.message}'))

    return openrouter_messages


class OpenRouterAgent(BaseMemberAgent):
    def __init__(self, name: str, member_id: str):
        super().__init__(name, member_id)
        self.llm = OpenRouterLLM(model)
        self.prompt = '你是一个AI助手，请回答用户的问题。'

    def get_ai_response(self, prompt: str, chat: AgentChat) -> str:
        messages = convert_to_openrouter_messages(chat)
        messages = [OpenAIMessage(role=Role.SYSTEM.value, content=prompt)] + messages
        return self.llm.invoke(messages)


if __name__ == '__main__':
    from langChainMA import LangchainMemberAgent

    agent = OpenRouterAgent('ai bot', 'openrouter_agent')
    # agent2: LangchainMemberAgent = LangchainMemberAgent('tom', 'tom')
    # agent.signup()
    agent.login()
    agent.socket.wait()
    # chat = AgentChat(member_id='openrouter_agent', messages=[], chat_id='xxx')
    # prompt = '你是一个AI助手，请回答用户的问题。'
    # message1 = agent2.produce_message('你好', 'xxx')
    # message2 = agent.produce_message('你好!很高兴能为你服务。请问有什么可以帮你的吗?', 'xxx')
    # message3 = agent2.produce_message('世界的发展趋势', 'xxx')
    # chat.add_message(message1)
    # chat.add_message(message2)
    # chat.add_message(message3)
    # response = agent.get_ai_response(prompt, chat)
    # print(response)

