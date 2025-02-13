from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton


class ChatInfoBar(QWidget):
    """聊天信息栏组件"""
    
    # 添加信号
    info_button_clicked = Signal()
    # 添加刷新信号
    refresh_needed = Signal(str)  # 参数为chat_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_chat_id = None
        self.setup_timer()
    
    def setup_timer(self):
        """设置定时器"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)  # 5秒刷新一次
        self.refresh_timer.timeout.connect(self.on_timer_timeout)
        self.refresh_timer.start()
    
    def on_timer_timeout(self):
        """定时器触发事件"""
        if self.current_chat_id:
            self.refresh_needed.emit(self.current_chat_id)
    
    def set_current_chat_id(self, chat_id: str):
        """设置当前聊天ID"""
        self.current_chat_id = chat_id
        # 重置定时器
        if chat_id:
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # 在线成员信息
        self.online_label = QLabel("在线: 0/0")
        self.online_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
            }
        """)

        # 群聊信息按钮
        self.info_button = QPushButton("群聊信息")
        self.info_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #DDDDDD;
                border-radius: 4px;
                padding: 5px 10px;
                color: #666666;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        # 连接点击事件
        self.info_button.clicked.connect(self.on_info_button_clicked)

        # 添加到布局
        layout.addWidget(self.online_label)
        layout.addStretch()  # 添加弹簧
        layout.addWidget(self.info_button)

        # 设置整体样式
        self.setStyleSheet("""
            ChatInfoBar {
                background-color: white;
                border-bottom: 1px solid #EEEEEE;
            }
        """)
        self.setFixedHeight(40)  # 固定高度

    def update_online_info(self, online_count: int, total_count: int):
        """更新在线人数信息"""
        self.online_label.setText(f"在线: {online_count}/{total_count}")

    def on_info_button_clicked(self):
        """群聊信息按钮点击事件"""
        if self.current_chat_id:  # 确保有选中的聊天
            self.info_button_clicked.emit()
        else:
            print('未选择chat')
