from PySide6.QtWidgets import (QWidget, QHBoxLayout, QTextEdit, QPushButton,
                             QVBoxLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent


class MessageInputBar(QWidget):
    """消息输入控件"""

    # 发送消息信号
    message_sent = Signal(str)  # 参数为消息内容

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # 创建主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 创建输入框
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("请输入消息...")
        self.input_edit.setMinimumHeight(60)
        self.input_edit.setMaximumHeight(120)
        self.input_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #DDDDDD;
                border-radius: 4px;
                padding: 10px;
                font-size: 20px;
                line-height: 1.5;
            }
            QTextEdit::placeholder {
                font-size: 20px;
                color: #999999;
            }
        """)

        # 设置默认字体
        font = self.input_edit.font()
        font.setPointSize(12)
        self.input_edit.setFont(font)

        # 创建发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setMinimumWidth(80)
        self.send_button.setFixedHeight(50)  # 设置固定高度
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #07C160;
                border: none;
                border-radius: 4px;
                padding: 12px 20px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #06AD56;
            }
            QPushButton:pressed {
                background-color: #059B4C;
            }
        """)

        # 创建按钮容器，使用垂直布局使按钮靠下
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()  # 添加弹簧使按钮靠下
        button_layout.addWidget(self.send_button)

        # 添加到主布局
        layout.addWidget(self.input_edit)
        layout.addWidget(button_container)

        # 连接信号
        self.send_button.clicked.connect(self.send_message)
        self.input_edit.installEventFilter(self)

        # 设置整体样式
        self.setStyleSheet("""
            MessageInputBar {
                background-color: white;
                border-top: 1px solid #EEEEEE;
            }
        """)
        self.setFixedHeight(150)

    def eventFilter(self, obj, event):
        """事件过滤器，处理按键事件"""
        if obj == self.input_edit and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                # Ctrl + Enter 发送消息
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def send_message(self):
        """发送消息"""
        text = self.input_edit.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
            self.input_edit.clear()
