import sys
import os

# 获取原始模块所在的目录路径
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../client'))
sys.path.append(module_path)
from client.memberAgent import MemberClientWithChats

import streamlit as st
import time
from client.dto import Message
import redis
import json
from datetime import datetime
import threading

# 设置页面为宽屏模式
st.set_page_config(layout="wide")


@st.cache_resource
def get_redis_client():
    return redis.Redis(host='localhost', port=6379, db=0)


# 获取Redis客户端
redis_client = get_redis_client()

# 定义Redis键
VILLAGERS_QUEUE = "werewolf:villagers:messages"
WOLVES_QUEUE = "werewolf:wolves:messages"


def serialize_message(message: Message) -> str:
    return json.dumps({
        'chat_id': message.chat_id,
        'from_member_id': message.from_member_id,
        'from_member_name': message.from_member_name,
        'message': message.message,
        'message_type': message.message_type,
        'message_id': message.message_id,
        'timestamp': message.timestamp if isinstance(message.timestamp, str) else message.timestamp.isoformat()
    })


def deserialize_message(message_str: str) -> Message:
    data = json.loads(message_str)
    # 确保所有必需字段都存在
    if isinstance(data['timestamp'], datetime):
        data['timestamp'] = data['timestamp'].isoformat()
    return Message(
        chat_id=data['chat_id'],
        from_member_id=data['from_member_id'],
        from_member_name=data['from_member_name'],
        message=data['message'],
        message_type=data.get('message_type', 'text'),  # 默认为text类型
        message_id=data.get('message_id', ''),  # 如果没有message_id，使用空字符串
        timestamp=data['timestamp']
    )


# 创建线程锁
message_lock = threading.Lock()

# 初始化消息列表
if 'villagers_messages' not in st.session_state:
    st.session_state.villagers_messages = []
if 'wolves_messages' not in st.session_state:
    st.session_state.wolves_messages = []

villagers_chat_id = 'b2acd6d3-4c61-4680-a012-be55bdd92d9b'
wolves_chat_id = '73dc7671-3da1-4a8a-afff-db3b6ed25a8d'
villager_ids = ['villager_001', 'villager_002', 'villager_003', 'villager_004', 'villager_005', 'villager_006',
                'villager_007', 'villager_008', 'villager_009', 'villager_010']


def display_message(msg: Message):
    with st.container():
        st.text(f"{msg.from_member_name}:")
        st.write(msg.message)
        st.text(f"时间: {msg.timestamp}")
        st.divider()


class Listener(MemberClientWithChats):
    def __init__(self, name: str, member_id: str):
        super().__init__(name, member_id)

    def on_login_success(self):
        super().on_login_success()
        # 登录成功后再监听聊天
        print('开始监听chat')
        self.listen_in_chat(villagers_chat_id)
        self.listen_in_chat(wolves_chat_id)

    def on_receive_message(self, message: Message):
        print(f'收到消息 - {message.chat_id}: {message.from_member_name}: {message.message}')
        super().on_receive_message(message)
        # 将消息存入Redis
        message_str = serialize_message(message)
        if message.chat_id == villagers_chat_id:
            redis_client.lpush(VILLAGERS_QUEUE, message_str)
            print(f'村民消息已加入队列，当前长度: {redis_client.llen(VILLAGERS_QUEUE)}')
        elif message.chat_id == wolves_chat_id:
            redis_client.lpush(WOLVES_QUEUE, message_str)
            print(f'狼人消息已加入队列，当前长度: {redis_client.llen(WOLVES_QUEUE)}')


# 初始化监听器
@st.cache_resource
def init_listener():
    listener = Listener(name='监听器', member_id='admin001')
    # 等待登录完成
    success = listener.login()
    if not success:
        st.error("监听器登录失败，请刷新页面重试")
        st.stop()
    return listener


listener = init_listener()

st.title("狼人杀游戏消息面板")

# 处理Redis中的消息
try:
    messages_processed = False
    new_villagers_messages = []
    new_wolves_messages = []
    processed_count = 0

    # 处理村民消息
    while True:
        message_str = redis_client.rpop(VILLAGERS_QUEUE)
        if not message_str:
            break
        message = deserialize_message(message_str.decode())
        messages_processed = True
        processed_count += 1
        print(f'处理村民消息({processed_count}) - {message.from_member_name}')
        if message not in st.session_state.villagers_messages:
            new_villagers_messages.append(message)

    # 处理狼人消息
    while True:
        message_str = redis_client.rpop(WOLVES_QUEUE)
        if not message_str:
            break
        message = deserialize_message(message_str.decode())
        messages_processed = True
        processed_count += 1
        print(f'处理狼人消息({processed_count}) - {message.from_member_name}')
        if message not in st.session_state.wolves_messages:
            new_wolves_messages.append(message)

    print(f'本次处理了 {processed_count} 条消息')

    # 一次性更新session state
    if new_villagers_messages:
        st.session_state.villagers_messages.extend(new_villagers_messages)
        print(f'添加了 {len(new_villagers_messages)} 条村民消息')

    if new_wolves_messages:
        st.session_state.wolves_messages.extend(new_wolves_messages)
        print(f'添加了 {len(new_wolves_messages)} 条狼人消息')

    if messages_processed:
        st.rerun()
except Exception as e:
    print(f"处理消息时出错: {e}")
    st.error(f"处理消息时出错: {e}")

# 创建两列布局，设置equal=True确保两列等宽
col1, col2 = st.columns(2, gap="large")

with col1:
    st.header("村民聊天")
    for msg in st.session_state.villagers_messages:
        display_message(msg)

with col2:
    st.header("狼人聊天")
    for msg in st.session_state.wolves_messages:
        display_message(msg)

# 创建底部控制栏
st.divider()
if st.button("清空消息", use_container_width=True):
    # 清空session state
    st.session_state.villagers_messages = []
    st.session_state.wolves_messages = []
    # 清空Redis队列
    redis_client.delete(VILLAGERS_QUEUE)
    redis_client.delete(WOLVES_QUEUE)
    print("已清空所有消息队列")
    st.rerun()

# 在底部显示当前消息数量的调试信息
st.divider()
st.write(f"当前村民消息数量: {len(st.session_state.villagers_messages)}")
st.write(f"当前狼人消息数量: {len(st.session_state.wolves_messages)}")

# 定期刷新以检查新消息
time.sleep(0.5)  # 减少刷新间隔
st.rerun()
