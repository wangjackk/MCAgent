import re
from enum import Enum, auto
from typing import List, Optional, Dict

from pydantic import BaseModel
from dto import Member
from langChainMA import LangchainMemberAgent
from memberClient import command
from memory import AgentChat

# 游戏规则说明
GameRule = """
狼人杀游戏规则：
游戏人数： 8人
游戏角色： 狼人x2,村民x4,预言家x1,女巫x1
进入夜晚时：狼人需要投票选择杀害一位玩家；预言家可以验证一位玩家身份；女巫有一次救人机会和杀人机会，一晚上只能选择救人或者杀人。
白天时：玩家依次发言，发言完毕后全员投票选择要驱逐的玩家。驱逐的玩家可发表遗言。
"""


class GameState(Enum):
    """游戏状态枚举"""
    INIT = auto()  # 游戏初始化阶段

    # 白天阶段
    DAY_START = auto()  # 白天开始
    DEATH_REPORT = auto()  # 死亡报告
    SPEECH = auto()  # 发言阶段
    VOTING = auto()  # 投票阶段
    VOTE_RESULT = auto()  # 投票结果
    WILL = auto()  # 遗言阶段

    # 夜晚阶段
    NIGHT_START = auto()  # 夜晚开始
    WOLF_KILL = auto()  # 狼人杀人阶段
    WOLF_KILL_RESULT = auto()  # 狼人杀人结果
    PROPHET_VERIFY = auto()  # 预言家验人阶段
    WITCH_SAVE = auto()  # 女巫救人阶段
    WITCH_KILL = auto()  # 女巫毒人阶段

    GAME_OVER = auto()  # 游戏结束 


class Role(Enum):
    """角色枚举"""
    WEREWOLF = '狼人'
    VILLAGER = '村民'
    PROPHET = '预言家'
    WITCH = '女巫'


class GameTime:
    """游戏时间管理"""

    def __init__(self, day_number: int = 1, is_day: bool = False):
        self.day_number = day_number  # 游戏从第1天开始
        self.is_day = is_day  # 游戏通常从晚上开始

    def next_phase(self):
        """进入下一个阶段（白天/黑夜交替）"""
        self.is_day = not self.is_day
        if self.is_day:
            self.day_number += 1
        print(f'游戏时间已更新:{self}')

    def current_phase(self) -> str:
        """获取当前阶段"""
        return "白天" if self.is_day else "夜晚"

    def __str__(self):
        return f"第{self.day_number}天，{self.current_phase()}"

    def set_time(self, day_number: int, is_day: bool):
        """设置时间"""
        self.day_number = day_number
        self.is_day = is_day

    def get_time(self) -> tuple[int, bool]:
        """获取时间信息"""
        return self.day_number, self.is_day


class VillagerInfo(Member):
    """玩家信息"""

    role: Role
    is_alive: bool


class DayInfo(BaseModel):
    """每日游戏信息记录"""
    # 第几天
    day_number: int = 1
    # 白天发言总结
    day_summary: Optional[str] = None
    # 被驱逐的 player name
    out: Optional[str] = None
    # 被狼人杀的
    killed_by_wolves: Optional[str] = None
    # 被女巫救的
    saved_by_witch: Optional[str] = None
    # 被女巫杀的
    killed_by_witch: Optional[str] = None
    # 被预言家验证的
    verified_by_prophet: Optional[dict] = None
    # 发言信息
    day_messages: List[str] = []
    night_messages: List[str] = []

    @staticmethod
    def create(day_number: int) -> 'DayInfo':
        """创建新的 DayInfo"""
        return DayInfo(day_number=day_number)

    def set_wolf_kill(self, target: str) -> 'DayInfo':
        """设置狼人击杀目标"""
        return self.copy_with(killed_by_wolves=target)

    def set_witch_save(self, target: str) -> 'DayInfo':
        """设置女巫救人目标"""
        return self.copy_with(saved_by_witch=target)

    def set_witch_kill(self, target: str) -> 'DayInfo':
        """设置女巫毒杀目标"""
        return self.copy_with(killed_by_witch=target)

    def set_prophet_verify(self, result: dict) -> 'DayInfo':
        """设置预言家验人结果"""
        return self.copy_with(verified_by_prophet=result)

    def set_vote_out(self, target: str) -> 'DayInfo':
        """设置投票放逐目标"""
        return self.copy_with(out=target)

    def add_night_message(self, message: str) -> 'DayInfo':
        """添加夜晚消息"""
        messages = self.night_messages or []
        messages.append(message)
        return self.copy_with(night_messages=messages)

    def add_day_message(self, message: str) -> 'DayInfo':
        """添加白天消息"""
        messages = self.day_messages or []
        messages.append(message)
        return self.copy_with(day_messages=messages)

    def copy_with(self, **kwargs) -> 'DayInfo':
        """创建当前对象的副本，并更新指定字段"""
        current_data = self.model_dump()
        current_data.update(kwargs)
        return DayInfo(**current_data)


def get_target(text: str, keyword: str) -> Optional[str]:
    """从文本中提取目标信息
    
    Args:
        text: 源文本
        keyword: 关键词
        
    Returns:
        提取到的目标信息，如果未找到则返回None
    """
    pattern = rf'\|{keyword}:([^|]+)\|'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def get_most_voted(votes: List[str]) -> Optional[str]:
    """获取得票最多的选项
    
    Args:
        votes: 投票列表
        
    Returns:
        得票最多的选项，如果列表为空则返回None
    """
    if not votes:
        return None

    vote_count = {}
    for vote in votes:
        vote_count[vote] = vote_count.get(vote, 0) + 1
    return max(vote_count, key=vote_count.get)


class PromptTemplate:
    """提示词模板管理"""

    # 基础角色提示模板
    BASE_ROLE_TEMPLATE = """{game_rule}
你是{name}, 正在参与狼人杀游戏。
你的身份是【{role}】
你的能力是【{ability}】
你的目标是【{target}】
讲话风格：{style}
发言要求：简短明了，条理清晰，不带任何前缀"""

    # 狼人特殊提示模板
    WEREWOLF_TEMPLATE = """{game_rule}
你是{name}, 正在参与狼人杀游戏。
你的身份是【{role}】
你的能力是【{ability}】
你的目标是【{target}】
你的狼人队友是：【{teammates}】(所有队友被淘汰时，请独自决定)
讲话风格：{style}
发言要求：简短明了，条理清晰，不带任何前缀"""

    # 投票阶段提示
    VOTE_TEMPLATE = """本轮发言已结束。
根据上述聊天记录进行投票。
候选人：{candidates}
要求：
1. 仔细分析每个玩家的发言
2. 给出投票理由
3. 在确定人选后输出格式：|VOTETO:NAME|"""

    # 遗言阶段提示
    LAST_WORDS_TEMPLATE = """你已被投票驱逐出局。
请发表你的遗言，可以：
1. 揭示自己的真实身份
2. 表达对其他玩家的看法
3. 给出你认为的凶手提示
要求：言简意赅，不超过100字"""

    # 狼人夜间讨论提示
    WOLF_NIGHT_TEMPLATE = """夜晚降临，现在是狼人内部讨论时间。
你的队友：{alive_wolves}
可选目标：{alive_players}
要求：
1. 与队友商议要袭击的目标
2. 分析每个玩家的可能身份
3. 确定目标后输出格式：|VOTETO:NAME|"""

    # 预言家验人提示
    PROPHET_VERIFY_TEMPLATE = """你作为预言家，现在可以验证一名玩家的身份。
可验证的玩家：{candidates}
已验证的玩家：{verified}(重要！！！)
要求：
1. 分析验证的必要性
2. 选择最有价值的目标
3. 确定后输出格式：|VERIFY:全名|"""

    # 女巫救人提示
    WITCH_SAVE_TEMPLATE = """你作为女巫，今晚可以使用药水。
今晚死亡的玩家是：{dead_villager}
你的药水状态：
- 解药：{has_save}
- 毒药：{has_kill}
存活玩家：{alive_villagers}
要求：
1. 分析使用药水的价值
2. 做出选择：
   - 使用解药：输出 "SAVE"
   - 使用毒药：输出 "|KILL:NAME|"
   - 放弃使用：输出 "GIVEUP"
注意：每晚只能使用一种药水"""

    @classmethod
    def get_base_prompt(cls, name: str, role: str, ability: str, target: str, style: str) -> str:
        """获取基础角色提示词"""
        return cls.BASE_ROLE_TEMPLATE.format(
            game_rule=GameRule,
            name=name,
            role=role,
            ability=ability,
            target=target,
            style=style
        )

    @classmethod
    def get_werewolf_prompt(cls, name: str, role: str, ability: str, target: str,
                            style: str, teammates: str) -> str:
        """获取狼人角色提示词"""
        return cls.WEREWOLF_TEMPLATE.format(
            game_rule=GameRule,
            name=name,
            role=role,
            ability=ability,
            target=target,
            style=style,
            teammates=teammates
        )

    @classmethod
    def get_vote_prompt(cls, candidates: List[str]) -> str:
        """获取投票阶段提示词"""
        return cls.VOTE_TEMPLATE.format(candidates=",".join(candidates))

    @classmethod
    def get_last_words_prompt(cls) -> str:
        """获取遗言阶段提示词"""
        return cls.LAST_WORDS_TEMPLATE

    @classmethod
    def get_wolf_night_prompt(cls, alive_wolves: List[str], alive_players: List[str]) -> str:
        """获取狼人夜间讨论提示词"""
        return cls.WOLF_NIGHT_TEMPLATE.format(
            alive_wolves=",".join(alive_wolves),
            alive_players=",".join(alive_players)
        )

    @classmethod
    def get_prophet_verify_prompt(cls, candidates: List[str], verified: Dict[str, str]) -> str:
        """获取预言家验人提示词"""
        verified_info = [f"{name}是{role}" for name, role in verified.items()]
        return cls.PROPHET_VERIFY_TEMPLATE.format(
            candidates=",".join(candidates),
            verified=",".join(verified_info) if verified_info else "无"
        )

    @classmethod
    def get_witch_save_prompt(cls, dead_villager: str, has_save: bool, has_kill: bool,
                              alive_villagers: List[str]) -> str:
        """获取女巫救人提示词"""
        return cls.WITCH_SAVE_TEMPLATE.format(
            dead_villager=dead_villager,
            has_save="可用" if has_save else "已用完",
            has_kill="可用" if has_kill else "已用完",
            alive_villagers=",".join(alive_villagers)
        )


class Villager(LangchainMemberAgent):
    """游戏玩家类
    
    继承自LangchainMemberAgent，代表游戏中的一个玩家角色。
    负责处理玩家的游戏行为，如投票、发言等。
    """

    def __init__(self, name: str, member_id: str, role: Role = Role.VILLAGER, style: str = '',
                 ability: str = '无特殊能力',
                 target: str = '找出狼人并投票驱逐，帮助好人阵营获得胜利',
                 villager_chat_id: str = None):
        """初始化村民
        
        Args:
            name: 玩家名称
            member_id: 玩家ID
            role: 玩家角色
            style: 发言风格
            ability: 玩家能力
            target: 玩家目标
            villager_chat_id: 村民会议聊天ID
        """
        super().__init__(name, member_id)

        # 游戏状态
        self.is_alive: bool = True
        self.role: Role = role

        # 角色属性
        self.ability = ability
        self.style = style
        self.target = target

        # 聊天相关
        self.villager_chat_id = villager_chat_id

        # 初始化提示词
        self.prompt = PromptTemplate.get_base_prompt(name, role.value, ability, target, style)

    def update_prompt(self):
        """更新玩家的提示词"""
        self.prompt = PromptTemplate.get_base_prompt(
            self.name,
            self.role.value,
            self.ability,
            self.target,
            self.style
        )

    @command()
    def vote(self, data: dict):
        """进行投票
        
        Args:
            data: 包含candidates(候选人列表)的数据字典
            
        Returns:
            str: 投票选择的目标玩家名称
        """
        candidates: List[str] = data['candidates']
        if self.name in candidates:
            candidates.remove(self.name)

        # 生成投票提示并添加到聊天
        vote_prompt = PromptTemplate.get_vote_prompt(candidates)
        vote_message = self.produce_message(vote_prompt, 'vote-prompt')

        # 创建临时聊天用于投票
        temp_chat = AgentChat(
            chat_id='temp-vote',
            member_id=self.member_id,
            messages=self.get_all_messages(self.villager_chat_id)
        )
        temp_chat.messages.append(vote_message)
        temp_chat.save_to_txt()
        # 获取AI响应并提取投票目标
        self.update_prompt()
        res = self.get_ai_response(self.prompt, temp_chat)
        print(f'{self.name}的回复: {res}')
        candidate = get_target(res, 'VOTETO')

        print(f'{self.name} 投票给: {candidate}')
        return candidate

    @command()
    def out(self, data: dict):
        """玩家出局
        
        Args:
            data: 命令数据字典
        """
        print(f'{self.name} 出局')
        self.is_alive = False

    @command('be-saved')
    def be_saved(self, data: dict):
        """玩家被救活
        
        Args:
            data: 命令数据字典
        """
        if self.is_alive:
            print(f'{self.name} 无需被救')
            return
        print(f'{self.name} 被救')
        self.is_alive = True

    @command('villager-info')
    def villager_info(self, data: dict) -> dict:
        """获取玩家信息
        
        Args:
            data: 命令数据字典
            
        Returns:
            dict: 包含玩家基本信息的字典
        """
        return {
            'name': self.name,
            'member_id': self.member_id,
            'role': self.role.value,
            'is_alive': self.is_alive
        }

    @command('clear-chat')
    def clear_chat(self, data: dict):
        """清空指定的聊天记录
        
        Args:
            data: 包含chat_id的数据字典
        """
        self.memory.clear_chat(data['chat_id'])


class Witch(Villager):
    """女巫角色类
    
    继承自Villager类，代表游戏中的女巫角色。
    女巫拥有一瓶解药和一瓶毒药，每种药只能使用一次。
    每晚只能使用一种药水。
    """

    def __init__(self, name: str, member_id: str, style: str, villager_chat_id: str):
        """初始化女巫角色
        
        Args:
            name: 玩家名称
            member_id: 玩家ID
            style: 发言风格
        """
        super().__init__(
            name=name,
            member_id=member_id,
            role=Role.WITCH,
            style=style,
            ability='每晚可以使用一瓶解药救人或使用一瓶毒药杀人，每种药水只能使用一次',
            target='找出狼人并投票驱逐，帮助好人阵营获得胜利',
            villager_chat_id=villager_chat_id
        )
        # 药水状态
        self.has_save: bool = True  # 是否还有解药
        self.has_kill: bool = True  # 是否还有毒药

    @command('save-or-kill')
    def save_or_kill(self, data: dict) -> str:
        """处理救人或杀人的选择
        
        Args:
            data: 包含死亡玩家信息和存活玩家列表的数据字典
            
        Returns:
            str: 行动选择结果，可能是 'SAVE'、'KILL:NAME' 或 'GIVEUP'
        """
        # 获取当晚死亡玩家和存活玩家信息
        dead_villager = data['dead-villager']
        alive_villagers = data['alive-villagers']

        # 生成女巫行动提示
        witch_prompt = PromptTemplate.get_witch_save_prompt(
            dead_villager=dead_villager,
            has_save=self.has_save,
            has_kill=self.has_kill,
            alive_villagers=alive_villagers
        )

        # 创建临时聊天用于决策
        temp_chat = AgentChat(
            chat_id='temp-witch',
            member_id=self.member_id,
            messages=self.get_all_messages(self.villager_chat_id)
        )

        # 添加提示到聊天记录
        message = self.produce_message(witch_prompt, 'witch-action')
        temp_chat.messages.append(message)

        # 获取AI响应并处理结果
        self.update_prompt()
        res = self.get_ai_response(self.prompt, temp_chat)
        print(f'女巫的回答: {res}')

        # 解析行动结果
        action = self.extract_action(res)
        print(f'女巫的行动: {action}')
        # 更新药水状态
        if action == 'SAVE':
            self.has_save = False
        elif action.startswith('KILL:'):
            self.has_kill = False

        return action

    def extract_action(self, text: str) -> Optional[str]:
        """从响应文本中提取行动选择

        Args:
            text: AI响应文本

        Returns:
            str: 提取的行动选择，可能是 'SAVE'、'KILL:NAME'、'GIVEUP' 或 None
        """
        # 匹配 SAVE 指令
        if 'SAVE' in text.upper():
            return 'SAVE'

        # 匹配 KILL:NAME 指令
        kill_target = get_target(text, 'KILL')
        if kill_target:
            return f'KILL:{kill_target}'

        # 匹配 GIVEUP 指令
        if 'GIVEUP' in text.upper():
            return 'GIVEUP'

        return None


class Prophet(Villager):
    """预言家角色类
    
    继承自Villager类，代表游戏中的预言家角色。
    预言家每晚可以验证一名玩家的身份。
    """

    def __init__(self, name: str, member_id: str, style: str, villager_chat_id: str):
        """初始化预言家角色
        
        Args:
            name: 玩家名称
            member_id: 玩家ID
            style: 发言风格
            villager_chat_id: 村民会议聊天ID
        """
        super().__init__(
            name=name,
            member_id=member_id,
            role=Role.PROPHET,
            style=style,
            ability='每晚可以验证一名玩家的身份',
            target='找出狼人并投票驱逐，帮助好人阵营获得胜利',
            villager_chat_id=villager_chat_id
        )
        # 已验证的玩家信息
        self.verify_dict: Dict[str, str] = {}

    @command('get-verify-target')
    def get_verify_target(self, data: dict) -> Optional[str]:
        """选择要验证的目标玩家
        
        Args:
            data: 包含候选玩家列表的数据字典
            
        Returns:
            str: 选择验证的玩家名称，如果没有选择则返回None
        """
        # 获取候选玩家列表
        candidates = data['candidates']

        # 移除自己和已经验证过的玩家
        if self.name in candidates:
            candidates.remove(self.name)
        for name in self.verify_dict:
            if name in candidates:
                candidates.remove(name)

        print(f'预言家验证候选: {candidates}')

        # 生成验证提示
        verify_prompt = PromptTemplate.get_prophet_verify_prompt(
            candidates=candidates,
            verified=self.verify_dict
        )

        # 创建临时聊天用于决策
        temp_chat = AgentChat(
            chat_id='temp-prophet',
            member_id=self.member_id,
            messages=self.get_all_messages(self.villager_chat_id)
        )
        # print('预言家的prompt:', verify_prompt)
        # 添加提示到聊天记录
        message = self.produce_message(verify_prompt, 'verify-target')
        temp_chat.messages.append(message)

        # 获取AI响应并提取验证目标
        self.update_prompt()
        res = self.get_ai_response(self.prompt, temp_chat)
        print('预言家思考:', res)

        return get_target(res, 'VERIFY')

    @command('verify-villager')
    def verify_villager(self, data: dict) -> bool:
        """记录验证结果
        
        Args:
            data: 包含被验证玩家信息的数据字典
            
        Returns:
            bool: 验证是否成功
        """
        target = data['name']
        role = data['role']

        # 记录验证结果
        self.verify_dict[target] = role
        print(f'预言家已验证：{target} 是 {role}')

        return True

    def update_prompt(self):
        """更新玩家的提示词"""
        self.prompt = PromptTemplate.get_base_prompt(
            self.name,
            self.role.value,
            self.ability,
            self.target,
            self.style
        ) + f'\n重要！！！已验证的村民身份：{self.verify_dict}'


class Werewolf(Villager):
    """狼人角色类
    
    继承自Villager类，代表游戏中的狼人角色。
    狼人可以在夜晚与队友讨论并选择一名玩家袭击。
    """

    def __init__(self, name: str, member_id: str, style: str, villager_chat_id: str, werewolf_chat_id: str):
        """初始化狼人角色
        
        Args:
            name: 玩家名称
            member_id: 玩家ID
            style: 发言风格
        """
        super().__init__(
            name=name,
            member_id=member_id,
            role=Role.WEREWOLF,
            style=style,
            ability='在夜晚可以与其他狼人商议后袭击一名玩家',
            target='在白天学会伪装隐藏自己的真实身份，与其他狼人合作，消灭所有好人阵营玩家',
            villager_chat_id=villager_chat_id
        )
        # 狼人相关
        self.teammates: List[str] = []  # 狼人队友列表
        self.host_member_id: str = None  # 用于获取狼人信息
        self.werewolf_chat_id = werewolf_chat_id

        # 狼人有两个chat,一个是村民会议,一个是狼人会议
        self.add_reference_chat(self.villager_chat_id, self.werewolf_chat_id)
        self.add_reference_chat(self.werewolf_chat_id, self.villager_chat_id)

    def update_prompt(self):
        """更新狼人的提示词，包含队友信息"""
        teammates_prompt = self.get_teammates_prompt()
        self.prompt = PromptTemplate.get_werewolf_prompt(
            name=self.name,
            role=self.role.value,
            ability=self.ability,
            target=self.target,
            style=self.style,
            teammates=teammates_prompt
        )

    @command('update-teammates')
    def update_teammates(self, data: dict):
        """更新狼人队友信息
        
        Args:
            data: 包含队友列表的数据字典
        """
        self.teammates = data['teammates']
        # 移除自己
        if self.name in self.teammates:
            self.teammates.remove(self.name)
        self.update_prompt()
        print(f'狼人{self.name}的队友: {self.teammates}')

    def get_teammates_prompt(self) -> str:
        """生成队友提示信息
        
        Returns:
            str: 格式化的队友信息字符串
        """
        if not self.teammates:
            return "所有队友已出局，你是最后的狼人"
        return ", ".join(self.teammates)
