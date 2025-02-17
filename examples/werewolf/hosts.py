import re
from typing import Callable, List, Optional, Dict, Tuple

from base import Role, GameState, GameTime, VillagerInfo, get_most_voted
from client.chatManager import BaseChatManager
from client.dto import Message
from daysInfoManager import DaysInfoManager


class BaseHost(BaseChatManager):
    """游戏主持基类
    
    负责管理村民信息和基本的游戏状态。
    """

    def __init__(self, name: str, member_id: str, villager_ids: List[str]):
        """初始化主持人
        
        Args:
            name: 主持人名称
            member_id: 主持人ID
            villager_ids: 村民ID列表
        """
        super().__init__(name, member_id)
        self.villager_ids = villager_ids
        self.villagers: List[VillagerInfo] = []
        self.game_time = GameTime()

    def update_villagers_info(self) -> List[VillagerInfo]:
        """更新所有村民信息"""
        villagers = []
        villagers_info = self.send_command('villager-info', self.villager_ids)
        # print(f'总计{len(villagers_info)}个村民信息, villagers_info: {villagers_info}')
        for villager_info in villagers_info:
            villager_dict = villager_info.result
            villager = VillagerInfo(**villager_dict)
            villagers.append(villager)

        self.villagers = villagers
        # print(f'已更新 villagers: {self.villagers}')
        return villagers

    def get_villager_info_by_id(self, member_id: str) -> Optional[VillagerInfo]:
        """根据ID获取村民信息"""
        self.update_villagers_info()
        for villager in self.villagers:
            if villager.member_id == member_id:
                return villager
        return None

    def get_villager_info_by_name(self, name: str) -> Optional[VillagerInfo]:
        """根据名称获取村民信息"""
        self.update_villagers_info()
        for villager in self.villagers:
            if villager.name == name:
                return villager
        return None

    def get_alive_villagers(self) -> List[VillagerInfo]:
        """获取所有存活村民"""
        self.update_villagers_info()
        return [villager for villager in self.villagers if villager.is_alive]

    def get_wolves(self) -> List[VillagerInfo]:
        """获取所有狼人村民"""
        self.update_villagers_info()
        return [villager for villager in self.villagers if villager.role == Role.WEREWOLF]

    def get_alive_wolves(self) -> List[VillagerInfo]:
        """获取所有存活的狼人"""
        self.update_villagers_info()
        return [villager for villager in self.villagers if villager.role == Role.WEREWOLF and villager.is_alive]

    def get_first_alive_player(self) -> Optional[VillagerInfo]:
        """获取第一个存活的村民"""

        alive_villagers = self.get_alive_villagers()
        return alive_villagers[0] if alive_villagers else None

    def get_next_alive_villager(self, current_villager_id: str) -> Optional[VillagerInfo]:
        """获取下一个存活的村民
        
        Args:
            current_villager_id: 当前村民ID
            
        Returns:
            Optional[VillagerInfo]: 下一个存活村民，如果没有则返回None
        """
        alive_villagers = self.get_alive_villagers()
        if not alive_villagers:
            return None

        try:
            current_index = next(i for i, p in enumerate(alive_villagers) if p.member_id == current_villager_id)
            # 如果还有下一个玩家，返回下一个；否则返回None
            if current_index + 1 < len(alive_villagers):
                return alive_villagers[current_index + 1]
            return None
        except StopIteration:
            return alive_villagers[0]  # 如果找不到当前ID，从第一个开始

    def get_next_alive_wolf(self, current_wolf_id: str) -> Optional[VillagerInfo]:
        """获取下一个存活的狼人
        狼人讨论时需要循环发言，直到达成一致
        """
        alive_wolves = self.get_alive_wolves()
        if not alive_wolves:
            return None

        try:
            current_index = next(i for i, p in enumerate(alive_wolves) if p.member_id == current_wolf_id)
            # 如果是最后一个，返回第一个（循环发言）
            if current_index + 1 >= len(alive_wolves):
                return alive_wolves[0]
            return alive_wolves[current_index + 1]
        except StopIteration:
            return alive_wolves[0]  # 如果找不到当前ID，从第一个开始

    def out(self, member_id: str):
        """村民出局
        
        Args:
            member_id: 出局玩家ID
        """
        self.send_command('out', [member_id])
        self.update_villagers_info()

    def check_game_over(self) -> bool:
        """检查游戏是否结束
        
        Returns:
            bool: 游戏是否结束
        """
        wolves = self.get_wolves()
        alive_wolves = [wolf for wolf in wolves if wolf.is_alive]

        alive_villagers = self.get_alive_villagers()
        alive_no_wolves = [villager for villager in alive_villagers if villager.role != Role.WEREWOLF]

        # 狼人全部出局，好人胜利
        if not alive_wolves:
            print('狼人阵营失败')
            return True

        # 狼人数量大于等于好人，狼人胜利
        if len(alive_no_wolves) <= len(alive_wolves):
            print('狼人阵营胜利')
            return True

        return False


class GameHost(BaseHost):
    """游戏主持人
    
    负责管理整个游戏流程，包括白天和夜晚的所有环节。
    使用状态模式管理不同阶段的游戏流程。
    """

    def __init__(self, name: str, member_id: str, villager_ids: List[str]=None):
        super().__init__(name, member_id, villager_ids)
        # 游戏状态
        self.game_state = GameState.INIT
        self.days_manager = DaysInfoManager()  # 使用 DaysInfoManager 替代 days_info 字典

        # 聊天频道
        self.villagers_chat_id: str = None  # 村民会议（所有人的公共频道）
        self.wolves_chat_id: str = None  # 狼人会议（狼人的私密频道）

        # 状态处理器映射
        self.handlers: Dict[GameState, Callable[[Message], None]] = {
            # 夜晚阶段
            GameState.NIGHT_START: self.handle_night_start,
            GameState.WOLF_KILL: self.handle_wolf_kill,

            # 白天阶段
            GameState.SPEECH: self.handle_speech_phase,
            GameState.VOTING: self.handle_voting_phase,
            GameState.WILL: self.handle_will_phase,
        }

    def init_game(self):
        """初始化游戏"""
        self.update_villagers_info()
        self.game_state = GameState.NIGHT_START  # 游戏从夜晚开始

    def on_receive_message(self, message: Message):
        super().on_receive_message(message)
        self.handle_message(message)

    def handle_message(self, message: Message):
        """处理收到的消息
        
        根据当前游戏状态处理玩家消息。
        
        Args:
            message: 收到的消息
        """
        if message.chat_id not in [self.villagers_chat_id, self.wolves_chat_id]:
            return
        # print(f'host 收到来自 {message.from_member_name} 的消息')
        handler: Callable[[Message], None] = self.handlers.get(self.game_state)
        # print(f'game_state: {self.game_state}, handler: {handler}')
        if handler:
            # print('handle message:', message.message)
            handler(message)
        else:
            print(f'host 收到消息：{message.message}，但没有任何处理函数')

    def handle_day_start(self, message: Message = None):
        """处理白天开始阶段"""
        self.game_state = GameState.DEATH_REPORT
        self.handle_death_report()

    def handle_death_report(self, message: Message = None):
        """处理死亡报告阶段
        只负责读取和公布夜晚的死亡信息，不执行动作
        """
        day_info = self.days_manager.get_day_info(self.game_time.day_number-1)
        print(f'第{self.game_time.day_number}天：', day_info)
        deaths = []

        # 读取狼人击杀信息
        if day_info.killed_by_wolves and not day_info.saved_by_witch:
            deaths.append(day_info.killed_by_wolves)

        # 读取女巫毒杀信息
        if day_info.killed_by_witch:
            deaths.append(day_info.killed_by_witch)

        # 公布死亡信息
        if deaths:
            death_msg = f'昨晚，{", ".join(deaths)} 玩家死亡。'
        else:
            death_msg = '昨晚是平安夜，没有玩家死亡。'
        self.send_message(death_msg, self.villagers_chat_id)

        if not self.check_game_over():
            # 进入发言阶段
            self.game_state = GameState.SPEECH
            first_player = self.get_first_alive_player()
            if first_player:
                self.choose_next_speaker(self.villagers_chat_id, first_player.member_id)

    def handle_vote_result(self, message: Message = None):
        """处理投票结果阶段"""
        most_voted_name = self.days_manager.get_day_info(self.game_time.day_number).out
        if most_voted_name:
            self.send_message(f'{most_voted_name} 被投票驱逐出局。', self.villagers_chat_id)
            most_voted_player = self.get_villager_info_by_name(most_voted_name)
            if most_voted_player:
                self.game_state = GameState.WILL
                self.choose_next_speaker(self.villagers_chat_id, most_voted_player.member_id)

    def handle_night_start(self, message: Message = None):
        """处理夜晚开始阶段"""
        self.start_wolf_discussion()

    def handle_wolf_kill(self, message: Message = None):
        """处理狼人杀人阶段"""
        if not message or message.chat_id != self.wolves_chat_id:
            return

        # 记录消息到当天的夜晚消息中
        self.add_night_message(self.game_time.day_number, message.message)

        # 检查是否是狼人讨论结束的信号
        message_upper = message.message.upper()
        if 'TERMINATE' in message_upper and 'ATTACK' in message_upper:
            self.game_state = GameState.WOLF_KILL_RESULT
            self.handle_wolf_kill_result(message)
            return

        # 选择下一位狼人发言
        next_wolf = self.get_next_alive_wolf(message.from_member_id)
        if next_wolf:
            self.choose_next_speaker(self.wolves_chat_id, next_wolf.member_id)

    def handle_wolf_kill_result(self, message: Message = None):
        """处理狼人杀人结果阶段"""
        killed_player = self.process_wolf_kill()
        if killed_player:
            # print(f'狼人击杀前的 day_info: {self.days_manager.get_day_info(self.game_time.day_number)}')
            self.days_manager.set_wolf_kill(self.game_time.day_number, killed_player)
            # print(f'狼人击杀后的 day_info: {self.days_manager.get_day_info(self.game_time.day_number)}')
            # 如果被狼人杀死，立即执行出局
            killed_player_info = self.get_villager_info_by_name(killed_player)
            if killed_player_info:
                self.out(killed_player_info.member_id)
        
        # 进入预言家验人阶段
        self.game_state = GameState.PROPHET_VERIFY
        self.handle_prophet_verify()

    def handle_prophet_verify(self) -> Optional[Dict[str, str]]:
        """处理预言家验人环节"""
        prophet = next((p for p in self.villagers if p.role == Role.PROPHET and p.is_alive), None)
        if not prophet:
            # 如果没有预言家，直接进入女巫阶段
            self.game_state = GameState.WITCH_SAVE
            self.handle_witch_save_or_kill()
            return None

        candidates = [p.name for p in self.get_alive_villagers() if p.name != prophet.name]
        if not candidates:
            raise RuntimeError("没有可验证的目标，游戏状态异常")

        command_results = self.send_command('get-verify-target', [prophet.member_id],
                                          {'candidates': candidates})
        print('command_results:', command_results)
        if not command_results:
            raise RuntimeError("预言家验人命令没有返回结果")

        verify_target = command_results[0].result
        if not verify_target:
            raise RuntimeError("预言家没有选择验证目标")

        target_player = self.get_villager_info_by_name(verify_target)
        if not target_player:
            raise RuntimeError(f"找不到被验证的玩家: {verify_target}")

        # 发送验证结果给预言家
        self.send_command('verify-villager', [prophet.member_id],
                         {'name': verify_target, 'role': target_player.role.value})
        
        # 记录验证结果
        result = {'name': verify_target, 'role': target_player.role.value}
        self.days_manager.set_prophet_verify(self.game_time.day_number, result)

        # 进入女巫阶段
        self.game_state = GameState.WITCH_SAVE
        self.handle_witch_save_or_kill()
        return result

    def handle_witch_save_or_kill(self, message: Message = None):
        """处理女巫阶段（包括救人和毒人）"""
        day_info = self.days_manager.get_day_info(self.game_time.day_number)
        # print(f'女巫行动前的 day_info: {day_info}')
        killed_player = day_info.killed_by_wolves
        witch = next((p for p in self.villagers if p.role == Role.WITCH and p.is_alive), None)

        if not witch:
            # 如果没有女巫，直接进入白天
            print('女巫已死亡，跳过')
            self.game_state = GameState.DAY_START
            self.game_time.next_phase()
            self.handle_day_start()
            return

        if killed_player:
            # 处理女巫的救人和毒人选择
            saved, poisoned = self.handle_witch_action(killed_player)
            if saved:
                # 如果救人，取消出局状态
                self.days_manager.set_witch_save(self.game_time.day_number, killed_player)
                saved_player = self.get_villager_info_by_name(killed_player)
                if saved_player:
                    self.send_command('be-saved', [saved_player.member_id])
            if poisoned:
                # 如果毒人，立即执行出局
                self.days_manager.set_witch_kill(self.game_time.day_number, poisoned)
                poisoned_player = self.get_villager_info_by_name(poisoned)
                if poisoned_player:
                    self.out(poisoned_player.member_id)
        
        # print(f'女巫行动后的 day_info: {self.days_manager.get_day_info(self.game_time.day_number)}')
        # 夜晚结束，进入白天
        self.game_state = GameState.DAY_START
        self.game_time.next_phase()
        # print(当前天数self.game_time.day_number)
        self.handle_day_start()

    def handle_speech_phase(self, message: Message):
        """处理发言阶段"""
        next_villager = self.get_next_alive_villager(message.from_member_id)
        if next_villager:
            self.choose_next_speaker(message.chat_id, next_villager.member_id)
        else:
            # 所有人发言完毕，进入投票阶段
            self.game_state = GameState.VOTING
            self.handle_voting_phase()

    def handle_voting_phase(self, message: Message = None):
        """处理投票阶段"""
        alive_players = self.get_alive_villagers()
        alive_player_ids = [p.member_id for p in alive_players]
        alive_player_names = [p.name for p in alive_players]

        votes_res = self.send_command('vote', alive_player_ids,
                                      {'candidates': alive_player_names})
        votes = [vote.result for vote in votes_res]

        most_voted_name = get_most_voted(votes)
        most_voted_player = self.get_villager_info_by_name(most_voted_name)

        self.out(most_voted_player.member_id)
        self.days_manager.set_vote_out(self.game_time.day_number, most_voted_name)

        if not self.check_game_over():
            # 进入遗言阶段
            self.game_state = GameState.WILL
            self.send_message(f'{most_voted_name} 被驱逐，请发表遗言。', self.villagers_chat_id)
            self.choose_next_speaker(self.villagers_chat_id, most_voted_player.member_id)

    def handle_will_phase(self, message: Message):
        """处理遗言阶段"""
        print(f'{message.from_member_name}已发表遗言:{message.message}')
        print('遗言阶段结束，准备进入夜晚')
        # 遗言结束，进入夜晚
        self.game_time.next_phase()
        self.start_night_phase()

    def start_wolf_discussion(self):
        """开始狼人讨论阶段"""
        print(f'开始狼人讨论，当前游戏时间：{self.game_time}')
        alive_wolves = self.get_alive_wolves()
        if not alive_wolves:
            print('异常：狼人全部出局，游戏结束')
            return

        alive_players = [p for p in self.get_alive_villagers() if p.role != Role.WEREWOLF]
        if not alive_players:
            print('异常：所有玩家都出局，游戏结束')
            return

        print(f'存活狼人：{[w.name for w in alive_wolves]}')
        print(f'可击杀目标：{[p.name for p in alive_players]}')

        self.game_state = GameState.WOLF_KILL
        # 在狼人会议中进行讨论
        wolf_names = [w.name for w in alive_wolves]
        target_names = [p.name for p in alive_players]

        # 主持人在狼人频道宣布开始
        self.send_message(
            f'狼人请睁眼。\n'
            f'今晚的狼人们：{", ".join(wolf_names)}\n'
            f'可以袭击的目标：{", ".join(target_names)}\n'
            f'请狼人们进行讨论，轮流发言，最后投票选择要袭击的目标。\n'
            f'在{wolf_names[-1]}发言时对之前的狼人队友发言进行汇总，请在消息中同时包含最终目标和"TERMINATE"，如："ATTACK 全名 TERMINATE"',
            self.wolves_chat_id
        )

        # 选择第一位狼人发言
        first_alive_wolf = alive_wolves[0]
        print(f'选择第一位狼人发言：{first_alive_wolf.name}')
        self.choose_next_speaker(self.wolves_chat_id, first_alive_wolf.member_id)

    def process_wolf_kill(self) -> Optional[str]:
        """处理狼人的击杀结果"""
        messages = self.memory.get_chat(self.wolves_chat_id).messages
        final_message = next((msg.message for msg in reversed(messages)
                              if 'TERMINATE' in msg.message.upper() and 'ATTACK' in msg.message.upper()), None)

        if not final_message:
            return None

        target = None
        match = re.search(r'ATTACK\s+([^\s]+)\s+TERMINATE', final_message.upper())
        if match:
            target = match.group(1)

        if target:
            self.send_message(f'狼人们一致决定袭击 {target}。狼人请闭眼。', self.wolves_chat_id)

        return target

    def handle_witch_action(self, killed_villager_name: str) -> Tuple[bool, Optional[str]]:
        """处理女巫救人和毒人环节"""
        witch = next((p for p in self.villagers if p.role == Role.WITCH and p.is_alive), None)
        if not witch:
            return False, None

        alive_villagers = [p.name for p in self.get_alive_villagers()]
        action = self.send_command('save-or-kill', [witch.member_id],
                                   {'dead-villager': killed_villager_name,
                                    'alive-villagers': alive_villagers})[0].result

        saved = action == 'SAVE'
        killed = action.split(':')[1] if action.startswith('KILL:') else None

        return saved, killed

    def start_night_phase(self):
        """开始夜晚阶段
        流程：狼人杀人 -> 预言家验人 -> 女巫救人/毒人 -> 天亮
        """
        print(f'进入夜晚阶段，当前游戏时间：{self.game_time}')
        self.game_state = GameState.NIGHT_START
        self.send_message('天黑请闭眼。', self.villagers_chat_id)
        # 开始狼人杀人环节
        self.start_wolf_discussion()

    def start_day_phase(self):
        """开始白天阶段
        流程：死亡公布 -> 玩家发言 -> 投票 -> 放逐 -> 遗言 -> 天黑
        """

        # 初始化新的一天的信息
        self.days_manager.get_day_info(self.game_time.day_number)
            
        self.game_state = GameState.DAY_START
        self.send_message('天亮了，请大家睁眼。', self.villagers_chat_id)
        self.handle_death_report()

    def add_night_message(self, day_number: int, message: str):
        """添加夜晚消息"""
        self.days_manager.add_night_message(day_number, message)
