
import json
from typing import List, Union

import openai
import requests
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from client.dto import Message
from client.memberAgent import BaseMemberAgent
from client.memory import AgentChat


@tool
def get_weather(city: str) -> str:
    """Use this to get weather information."""
    url = f'https://restapi.amap.com/v3/weather/weatherInfo?city={city}&key=xxx'
    res = requests.get(url)
    data = json.loads(res.content.decode())
    info = data['lives'][0]
    # 指定要保留的键
    keys_to_keep = ['province', 'city', 'weather', 'temperature', 'winddirection', 'windpower', 'humidity', ]

    # 使用字典推导式创建新字典
    weather = {key: info[key] for key in keys_to_keep}
    return str(weather)


@tool
def test_tool(a: str) -> str:
    """
    测试函数工具,无实际作用
    """

    return f'test ok, arg:{a}'


def convert_to_langchain_messages(agent_chat: AgentChat) -> List[Union[HumanMessage, AIMessage]]:
    """
    将 AgentChat 中的消息转换为 langchain 的 message 格式。
    """
    langchain_messages = []
    for message in agent_chat.messages:
        if message.from_member_id == agent_chat.member_id:
            langchain_messages.append(AIMessage(content=message.message))
        else:
            langchain_messages.append(HumanMessage(content=f'{message.from_member_name}: {message.message}'))

    return langchain_messages


class LangchainMemberAgent(BaseMemberAgent):
    def __init__(self, name: str, member_id: str):
        super().__init__(name, member_id)

        self.model = ChatOpenAI(model='gpt-4o',
                                api_key='')

        # self.model = ChatOpenAI(api_key='xxx',
        #                         model = 'deepseek-ai/DeepSeek-R1',
        #                         base_url='https://api.siliconflow.cn')
        # self.model = ChatOpenAI(model='google/gemini-2.0-flash-001',
        #                         api_key='xxx',
        #                         base_url='https://openrouter.ai/api/v1')
        # self.agent = create_react_agent(self.model, tools=[test_tool])

        self.prompt = f'你正在参加群聊，你叫{self.name},擅长聊天,扮演真人,直接回复消息，无需添加名字前缀.其他人消息格式:[Name:message]'

    @retry(
        stop=stop_after_attempt(10),  # 最多重试3次
        wait=wait_exponential(multiplier=2, min=5, max=120),  # 指数退避重试间隔
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError, openai.RateLimitError))  # 指定需要重试的异常类型
    )
    def get_ai_response(self, prompt: str, chat: AgentChat) -> str:
        mes = convert_to_langchain_messages(chat)
        messages = [SystemMessage(prompt)] + mes
        # ret = self.model.invoke({"messages": messages})
        ret = self.model.invoke(messages)
        rsp = ret.content
        # print('ret:', ret, type(ret))
        # rsp = ret['messages'][-1].content
        return rsp


if __name__ == '__main__':
    tom = LangchainMemberAgent('tom', 'admin001')
    jack = LangchainMemberAgent('jack', 'ai001')
    # jack.signup()
    jack.login()
    success = tom.login()
    print(tom.get_joined_chats())
    if not success:
        print('connect failed')
        exit()

    tom.socket.wait()
