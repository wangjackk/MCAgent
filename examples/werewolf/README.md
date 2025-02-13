# AI Werewolf Game Example

这是一个基于MCAgent框架实现的多智能体狼人杀游戏。该示例展示了如何使用框架构建一个复杂的多智能体交互系统，每个AI智能体都具有独特的性格和行为模式。

## 游戏特点

1. 多智能体协作与对抗
2. 个性化AI角色
3. 实时多人交互
4. 复杂状态管理
5. 多频道通信
6. 基于LangChain的智能对话

## 项目结构

- `base.py`: 基础类和游戏状态定义
- `hosts.py`: 游戏主持人实现
- `daysInfoManager.py`: 游戏日程管理
- `game_ui.py`: 游戏界面
- `werewolfGame.py`: 游戏主程序

## 角色设计

### 1. 游戏主持人
- 管理游戏流程
- 控制游戏状态
- 处理投票和结果
- 发布游戏信息

### 2. 玩家角色
- 狼人（Werewolf）
  - 夜晚可以与其他狼人商议杀人
  - 需要在白天隐藏身份
- 预言家（Prophet）
  - 每晚可以查验一名玩家身份
  - 需要合理利用信息
- 女巫（Witch）
  - 拥有一瓶解药和一瓶毒药
  - 每晚只能使用一种药水
- 村民（Villager）
  - 通过推理找出狼人
  - 参与投票决策

## 游戏流程

### 夜晚阶段
1. 狼人杀人
2. 预言家验人
3. 女巫救人/毒人

### 白天阶段
1. 死亡信息公布
2. 玩家依次发言
3. 投票环节
4. 放逐玩家
5. 遗言环节

## 特色功能

### 1. 个性化对话系统
```python
styles = [
    "说话风格幽默，喜欢以'天哪！'开头",
    "是个逗逼，总能把严肃的问题讲得像脱口秀一样有趣",
    "一个文艺中二青年，总是沉浸在自己的诗歌和幻想中"
    # ...
]
```

### 2. 状态管理
```python
class GameState(Enum):
    INIT = auto()
    DAY_START = auto()
    DEATH_REPORT = auto()
    SPEECH = auto()
    VOTING = auto()
    # ...
```

### 3. 多频道通信
- 村民大厅（所有人可见）
- 狼人频道（仅狼人可见）
- 系统通知（游戏信息发布）

## 使用方法

1. 确保已安装依赖：
```bash
pip install langchain openai pydantic
```

2. 配置环境：
```python
# 设置API密钥
os.environ["OPENAI_API_KEY"] = "your-api-key"
```

3. 运行游戏：
```python
python werewolfGame.py
```

## 示例代码

```python
# 创建游戏主持人
host = GameHost(name='主持人', member_id='werewolf_host')
host.login()

# 创建玩家
villager = Villager(name='天真无邪小可爱', member_id='villager_001', style=styles[0])
werewolf = Werewolf(name='诗魂李白', member_id='villager_003', style=styles[2])
prophet = Prophet(name='预言家张三', member_id='villager_004', style=styles[3])

# 开始游戏
host.init_game()
```

## 扩展建议

1. 添加更多角色（如守卫、猎人等）
2. 实现游戏回放功能
3. 添加更多游戏模式
4. 增强AI的策略性
5. 添加游戏数据分析
6. 实现观战模式

## 技术亮点

1. **分布式多智能体系统**
   - 每个Agent可以在不同机器上独立运行
   - 支持跨网络、跨平台协作
   - 可扩展性强，轻松添加新Agent
   - 天然支持负载均衡
   - 适合大规模AI集群部署

2. **状态机设计**
   - 清晰的游戏流程控制
   - 灵活的状态转换
   - 完整的生命周期管理

3. **AI角色设计**
   - 个性化提示词系统
   - 基于上下文的对话生成
   - 策略性决策能力

4. **事件系统**
   - 实时消息处理
   - 多频道通信
   - 状态同步机制

5. **记忆管理**
   - 游戏历史记录
   - 角色行为追踪
   - 上下文维护

## 注意事项

1. 需要有效的API密钥
2. 建议使用GPT-4或更高版本的模型
3. 注意控制API调用频率
4. 游戏需要足够的玩家数量
5. 建议在开发模式下调试AI行为

## 贡献指南

欢迎提交Issue和Pull Request来改进游戏：
1. 新增游戏角色
2. 优化AI策略
3. 改进游戏流程
4. 修复已知问题
5. 增加新功能
