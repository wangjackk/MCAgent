# MCAgent Framework

MCAgent是一个强大的分布式多智能体框架，专注于构建复杂的人机协作系统。它支持多个AI智能体和人类用户在分布式环境中进行实时交互，特别适合开发需要多方协作的应用场景。

## 核心特性

### 1. 分布式架构
- 每个Agent可以在不同机器上独立运行
- 支持跨网络、跨平台协作
- 可扩展性强，轻松添加新Agent
- 天然支持负载均衡
- 适合大规模AI集群部署

### 2. 实时通信
- 基于Socket.IO的实时消息系统
- 多频道通信支持
- 事件驱动的消息处理
- 自动的状态同步
- 可靠的消息传递

### 3. 智能体管理
- 灵活的角色定义
- 个性化的Agent行为
- 基于LangChain的对话能力
- 可定制的决策逻辑
- 支持多种AI模型

### 4. 交互控制
- Chat Manager机制
- 动态的发言控制
- 支持多种交互策略
- 人机自然混合对话
- 场景化的交互流程

## 应用场景

### 1. 游戏与娱乐
- 多人在线游戏（如狼人杀）
- 角色扮演游戏
- AI游戏主持人
- 智能NPC系统
- 互动故事生成

### 2. 企业协作
- 文档审批工作流
- 团队协作系统
- 智能客服平台
- 会议管理助手
- 项目管理工具

### 3. 教育培训
- 智能导师系统
- 模拟训练环境
- 协作学习平台
- 知识问答系统
- 技能评估工具

### 4. 社交媒体
- AI社群管理
- 智能群聊系统
- 内容审核平台
- 社交机器人
- 用户行为分析

### 5. 研究与实验
- 多智能体仿真
- 群体行为研究
- AI策略评估
- 人机交互实验
- 社会计算模型

## 框架结构

### 1. 核心组件
```
client/
  ├── memberClient.py     # 基础客户端
  ├── memberAgent.py      # Agent基类
  ├── chatManager.py      # 聊天管理器
  ├── events.py          # 事件定义
  └── memory.py          # 记忆系统
```

### 2. 示例项目
```
examples/
  ├── chatroom/          # 智能聊天室
  ├── werewolf/          # 狼人杀游戏
  └── .../               
```

## 核心概念

MCAgent框架基于以下核心概念设计：

### 1. Member（成员）
- 每个参与者都是一个Member
- 具有唯一的member_id和name
- 需要signup注册和login登录
- 可以发送和接收消息

### 2. Agent（智能体）
- 继承自Member
- 分为人类Agent和AI Agent

### 3. Chat（聊天）
- 对话的容器
- 包含多个Member
- 有唯一的chat_id
- 记录对话历史

### 4. Manager（管理器）
- 控制对话流程
- 管理成员加入/退出
- 创建和维护Chat
- 决定发言顺序

### 5. 消息流转
1. Member发送消息到Chat
2. Manager接收到消息
3. Manager选择下一个发言者
4. 下一个发言者收到reply请求
5. 生成回复并发送消息
6. 循环继续

### 6. 事件系统
- 基于Socket.IO
- 实时消息传递
- 支持异步通信
- 自动状态同步

### 7. 记忆系统
- 保存对话历史
- 维护成员状态
- 支持上下文理解
- 可持久化存储

## 简单教程

让我们创建一个简单的命令行对话系统，包含一个人类用户、一个AI助手和一个对话管理器。

### 1. 创建Human Agent
```python
from client.memberAgent import BaseMemberAgent
from client.dto import ReplyData

class HumanAgent(BaseMemberAgent):
    def __init__(self, name, member_id):
        super().__init__(name, member_id)

    def reply(self, data: ReplyData):
        chat_id = data.chat_id
        input_text = input('请输入你的发言:')
        self.send_message(input_text, chat_id)
```

### 2. 创建AI Agent
```python
from client.langChainMA import LangchainMemberAgent

class AIAssistant(LangchainMemberAgent):
    def __init__(self, name: str, member_id: str):
        super().__init__(name, member_id)
        self.prompt = """你是一个友好的AI助手，负责:
                        1. 回答用户问题
                        2. 提供帮助建议
                        3. 保持对话友好"""
```

### 3. 运行对话系统
```python
from client.chatManager import ChatManager


# 创建参与者
human = HumanAgent("Human", "human_001")
assistant = AIAssistant("Bot", "ai_001")
manager = ChatManager("Manager", "manager_001")

# 注册用户 (只需要执行一次)
# human.signup()
# assistant.signup()
# manager.signup()

# 登录
human.login()
assistant.login()
manager.login()

# 创建聊天 (只需要执行一次，之后只需要chat_id)
# _, chat = manager.create_chat(
#     name="测试聊天",
#     description="人机对话测试",
# )
# chat_id = chat.chat_id
chat_id = '6adde71f-f30d-442a-8cab-897b8f8365f3'  # 使用已创建的chat_id

# 拉人进群
manager.pull_members_into_chat(chat_id, [human.member_id, assistant.member_id])

# 开始对话
human.send_message("你好", chat_id)
human.socket.wait()


```

这个示例展示了框架的核心功能：
1. Human Agent处理用户输入
2. AI Agent使用LangChain进行对话生成
3. 使用框架自带的ChatManager管理对话
4. 简单直观的对话流程

运行后，系统会：
1. 登录所有参与者
2. 将成员加入聊天
3. 发送初始消息并等待响应
4. 自动管理对话顺序

## 开发指南

### 1. 创建新Agent
```python
class MyAgent(BaseMemberAgent):
    def __init__(self, name: str, member_id: str):
        super().__init__(name, member_id)
        self.prompt = "自定义提示词"
```

### 2. 自定义Manager
```python
class MyManager(BaseChatManager):
    def get_next_speaker(self, message: Message):
        # 实现自己的发言选择逻辑
        return next_speaker_id
```

### 3. 添加新事件
```python
class Events:
    MY_EVENT = 'my_event'
```

## 最佳实践

1. **分布式部署**
   - 根据负载分配Agent
   - 使用合适的通信策略
   - 注意状态同步

2. **交互设计**
   - 设计清晰的交互流程
   - 处理异常情况
   - 提供自然的体验

3. **性能优化**
   - 控制消息频率
   - 管理内存使用
   - 优化响应时间

4. **安全考虑**
   - 实现权限控制
   - 保护敏感数据
   - 防止滥用

## 贡献指南

欢迎贡献代码和想法！请参考以下步骤：

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 启动服务器
```bash
python server/main.py
```

3. 运行示例
```bash
# 运行聊天室示例
python examples/chatroom/main.py

# 运行狼人杀游戏
python examples/werewolf/main.py

# 运行工作流示例
python examples/workflow/main.py
```

## 特色功能

### 1. Chat Manager机制
- 每个聊天都有专门的管理者
- 控制发言顺序和权限
- 支持多种管理策略
- 动态调整交互流程

### 2. 人机混合交互
- 人类可以随时参与对话
- 系统动态调整响应
- 自然的交互体验
- 灵活的角色切换

### 3. 记忆管理
- 上下文感知
- 历史记录追踪
- 多频道记忆
- 可持久化存储

### 4. 事件系统
- 实时事件处理
- 自定义事件支持
- 事件链路追踪
- 异步事件处理
