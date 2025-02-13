from typing import Dict, Optional, List
from base import DayInfo


class DaysInfoManager:
    """游戏日志管理器
    
    负责管理和维护游戏中每一天的信息记录。
    提供添加、获取和更新日志的方法。
    """
    
    def __init__(self):
        """初始化日志管理器"""
        self.days_info: Dict[int, DayInfo] = {}
        
    def get_day_info(self, day_number: int) -> DayInfo:
        """获取或创建指定天数的 DayInfo
        
        Args:
            day_number: 游戏天数
            
        Returns:
            DayInfo: 该天的游戏信息
        """
        if day_number not in self.days_info:
            self.days_info[day_number] = DayInfo.create(day_number)
        return self.days_info[day_number]
        
    def update_day_info(self, day_number: int, **kwargs) -> DayInfo:
        """更新指定天数的 DayInfo
        
        Args:
            day_number: 游戏天数
            **kwargs: 要更新的字段和值
            
        Returns:
            DayInfo: 更新后的游戏信息
        """
        day_info = self.get_day_info(day_number)
        self.days_info[day_number] = day_info.copy_with(**kwargs)
        return self.days_info[day_number]
        
    def set_wolf_kill(self, day_number: int, killed_player: str) -> DayInfo:
        """设置狼人击杀的玩家
        
        Args:
            day_number: 游戏天数
            killed_player: 被击杀玩家的名称
            
        Returns:
            DayInfo: 更新后的游戏信息
        """
        day_info = self.get_day_info(day_number)
        self.days_info[day_number] = day_info.set_wolf_kill(killed_player)
        return self.days_info[day_number]
        
    def set_witch_save(self, day_number: int, saved_player: str) -> DayInfo:
        """设置女巫救的玩家
        
        Args:
            day_number: 游戏天数
            saved_player: 被救玩家的名称
            
        Returns:
            DayInfo: 更新后的游戏信息
        """
        day_info = self.get_day_info(day_number)
        self.days_info[day_number] = day_info.set_witch_save(saved_player)
        return self.days_info[day_number]
        
    def set_witch_kill(self, day_number: int, killed_player: str) -> DayInfo:
        """设置女巫毒死的玩家
        
        Args:
            day_number: 游戏天数
            killed_player: 被毒死玩家的名称
            
        Returns:
            DayInfo: 更新后的游戏信息
        """
        day_info = self.get_day_info(day_number)
        self.days_info[day_number] = day_info.set_witch_kill(killed_player)
        return self.days_info[day_number]
        
    def set_prophet_verify(self, day_number: int, verify_result: Dict[str, str]) -> DayInfo:
        """设置预言家验证的结果
        
        Args:
            day_number: 游戏天数
            verify_result: 验证结果
            
        Returns:
            DayInfo: 更新后的游戏信息
        """
        day_info = self.get_day_info(day_number)
        self.days_info[day_number] = day_info.set_prophet_verify(verify_result)
        return self.days_info[day_number]
        
    def set_vote_out(self, day_number: int, voted_player: str) -> DayInfo:
        """设置被投票出局的玩家
        
        Args:
            day_number: 游戏天数
            voted_player: 被投票出局玩家的名称
            
        Returns:
            DayInfo: 更新后的游戏信息
        """
        day_info = self.get_day_info(day_number)
        self.days_info[day_number] = day_info.set_vote_out(voted_player)
        return self.days_info[day_number]
        
    def add_night_message(self, day_number: int, message: str) -> DayInfo:
        """添加夜晚消息
        
        Args:
            day_number: 游戏天数
            message: 要添加的消息
            
        Returns:
            DayInfo: 更新后的游戏信息
        """
        day_info = self.get_day_info(day_number)
        self.days_info[day_number] = day_info.add_night_message(message)
        return self.days_info[day_number] 