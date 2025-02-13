from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea,
                           QLabel, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime
import uuid

from dto import Message

from examples.chatroom.globals import get_human_agent


class MessageBubble(QFrame):
    """单个消息气泡组件"""
    
    BUBBLE_STYLE = """
        QLabel {{
            background-color: {color};
            border-radius: 10px;
            padding: 10px;
        }}
    """
    
    TIMESTAMP_STYLE = "color: gray; font-size: 12px;"
    PADDING = 30  # 消息内容左右padding
    
    def __init__(self, message: Message, is_self: bool, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_self = is_self
        self.setup_ui()
        self.updateMaxWidth()
    
    def setup_ui(self):
        """初始化UI组件"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        
        layout = QVBoxLayout()
        layout.setSpacing(4)
        
        # 添加发送者名称
        self.setup_name_label(layout)
        
        # 添加消息内容
        self.setup_message_container(layout)
        
        # 添加时间戳
        self.setup_timestamp_label(layout)
        
        self.setLayout(layout)
    
    def setup_name_label(self, layout):
        """设置发送者名称标签"""
        name_label = QLabel(self.message.from_member_name)
        name_label.setAlignment(Qt.AlignLeft if not self.is_self else Qt.AlignRight)
        layout.addWidget(name_label)
    
    def setup_message_container(self, layout):
        """设置消息内容容器"""
        self.msg_container = QWidget()
        msg_layout = QHBoxLayout(self.msg_container)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建消息标签
        self.msg_label = QLabel(self.message.message)
        self.msg_label.setWordWrap(True)
        self.msg_label.setStyleSheet(
            self.BUBBLE_STYLE.format(color="#95EC69" if self.is_self else "white")
        )
        
        # 设置对齐方式
        if self.is_self:
            msg_layout.addStretch()
        msg_layout.addWidget(self.msg_label)
        if not self.is_self:
            msg_layout.addStretch()
            
        layout.addWidget(self.msg_container)
    
    def format_timestamp(self, timestamp: str) -> str:
        """格式化时间戳，只显示到秒，并转换为本地时间"""
        try:
            # 解析为 datetime 对象
            dt = datetime.fromisoformat(timestamp)
            # 转换为本地时间
            local_dt = dt.astimezone()  # 自动使用系统时区
            # 格式化时间，只显示到秒
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"时间戳解析失败: {e}")
            return timestamp  # 如果解析失败，返回原始时间戳
    
    def setup_timestamp_label(self, layout):
        """设置时间戳标签"""
        formatted_time = self.format_timestamp(self.message.timestamp)
        
        # 转换为本地时间（假设本地时区是 UTC+8）
        time_label = QLabel(formatted_time)
        time_label.setAlignment(Qt.AlignLeft if not self.is_self else Qt.AlignRight)
        time_label.setStyleSheet(self.TIMESTAMP_STYLE)
        layout.addWidget(time_label)


    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.updateMaxWidth()
    
    def updateMaxWidth(self):
        """更新消息气泡宽度"""
        window_width = self.window().width()
        target_width = int(window_width * 0.4)
        
        # 计算单行文本宽度
        font_metrics = self.msg_label.fontMetrics()
        text = self.msg_label.text()
        single_line_width = font_metrics.horizontalAdvance(text) + self.PADDING
        
        # 根据文本长度决定是否换行
        if single_line_width <= target_width:
            self.msg_label.setWordWrap(False)
            width = single_line_width
        else:
            self.msg_label.setWordWrap(True)
            width = target_width
        
        self.msg_label.setFixedWidth(width)


class MessagesWidget(QWidget):
    """消息列表窗口"""
    
    SCROLL_AREA_STYLE = """
        QScrollArea {
            border: none;
            background-color: #F5F5F5;
        }
    """
    
    CONTAINER_STYLE = "background-color: #F5F5F5;"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.human_agent = get_human_agent()
        self.message_bubbles = []
        self.setup_ui()
    
    def setup_ui(self):
        """初始化UI组件"""
        self.setup_layout()
        self.setup_scroll_area()
        self.setup_messages_container()
        self.initUI()
    
    def setup_layout(self):
        """设置主布局"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
    
    def setup_scroll_area(self):
        """设置滚动区域"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(self.SCROLL_AREA_STYLE)
    
    def setup_messages_container(self):
        """设置消息容器"""
        self.messages_container = QWidget()
        self.messages_container.setStyleSheet(self.CONTAINER_STYLE)
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_container)
        self.main_layout.addWidget(self.scroll_area)
    
    def initUI(self):
        """初始化窗口属性"""
        self.setWindowTitle('消息显示')
        self.resize(600, 800)
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.update_all_bubbles_width()
    
    def update_all_bubbles_width(self):
        """更新所有消息气泡的宽度"""
        for bubble in self.message_bubbles:
            bubble.updateMaxWidth()
    
    def add_message(self, message: Message):
        """添加新消息"""
        bubble = MessageBubble(message, message.from_member_id == self.human_agent.member_id)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self.message_bubbles.append(bubble)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """滚动到底部"""
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def clear_messages(self):
        """清空所有消息"""
        for bubble in self.message_bubbles:
            bubble.deleteLater()
        self.message_bubbles.clear()

    def load_messages(self, chat_id: str):
        """从服务器加载指定聊天的消息"""
        self.clear_messages()
        messages = self.human_agent.load_chat_messages_from_server(chat_id, 5)
        # print(f'load messages {len(messages)} :', messages)

        member_id_to_name = {}
        for message in messages:
            # 检查message是否已经是Message对象
            if not isinstance(message, Message):
                message = Message(**message)
            
            if message.from_member_name == '' or message.from_member_name is None:
                if message.from_member_id not in member_id_to_name:
                    member_id_to_name[message.from_member_id] = self.human_agent.get_member(message.from_member_id).name
                message.from_member_name = member_id_to_name[message.from_member_id]
            self.add_message(message)
        self.scroll_to_bottom()

    def add_test_messages(self):
        """添加一些测试消息"""
        test_messages = [
            Message(
                message="你好！",
                message_type="text",
                chat_id="test_chat",
                from_member_id="other_user",
                from_member_name="其他用户",
                timestamp=str(datetime.now()),
                message_id=str(uuid.uuid4())
            ),
            Message(
                message="你好！很高兴见到你",
                message_type="text",
                chat_id="test_chat",
                from_member_id=self.human_agent.member_id,
                from_member_name=self.human_agent.name,
                timestamp=str(datetime.now()),
                message_id=str(uuid.uuid4())
            ),
            Message(
                message="今天天气真不错！",
                message_type="text",
                chat_id="test_chat",
                from_member_id="other_user",
                from_member_name="其他用户",
                timestamp=str(datetime.now()),
                message_id=str(uuid.uuid4())
            ),
        ]

        for message in test_messages:
            self.add_message(message)
