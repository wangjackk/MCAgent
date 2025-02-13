from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from joinedChatsWindow import JoinedChatsWindow
from messagesWidget import MessagesWidget
from chatInfoBar import ChatInfoBar
from chatInfoDialog import ChatInfoDialog
from messageInputBar import MessageInputBar
import globals


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化全局human_agent
        self.human_agent = globals.get_human_agent()

        # 创建中心部件
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # 创建主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建左侧聊天列表窗口
        self.chats_window = JoinedChatsWindow(self)
        self.chats_window.setMaximumWidth(400)

        # 创建右侧布局
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 创建顶部信息栏
        self.chat_info_bar = ChatInfoBar()
        self.chat_info_bar.info_button_clicked.connect(self.show_chat_info)
        self.chat_info_bar.refresh_needed.connect(self.refresh_chat_info)
        right_layout.addWidget(self.chat_info_bar)
        
        # 创建消息窗口
        self.messages_widget = MessagesWidget(self)
        right_layout.addWidget(self.messages_widget)
        
        # 创建消息输入栏
        self.message_input = MessageInputBar()
        self.message_input.message_sent.connect(self.send_message)
        right_layout.addWidget(self.message_input)

        # 添加到主布局
        self.main_layout.addWidget(self.chats_window)
        self.main_layout.addWidget(right_widget)

        # 连接聊天列表的选择事件
        self.chats_window.chats_list.currentItemChanged.connect(self.on_chat_selected)

        # 连接消息信号
        self.human_agent.message_received.connect(self.on_message_received)
        self.human_agent.message_sent.connect(self.on_message_sent)

        # 连接登录成功信号
        self.human_agent.login_succeed.connect(self.on_login_success)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('聊天客户端')
        self.resize(1200, 800)
        # self.setWindowState(Qt.WindowMaximized)

    def refresh_chat_info(self, chat_id: str):
        """刷新聊天信息"""
        if chat_id:
            members = self.human_agent.get_chat_members(chat_id, True, False)
            online_members = self.human_agent.get_chat_online_members(chat_id)
            # print('update online/members')
            self.chat_info_bar.update_online_info(len(online_members), len(members))
    
    def on_chat_selected(self, current, previous):
        """当选择的聊天改变时触发"""
        if current:
            chat_id = self.chats_window.get_selected_chat_id()
            if chat_id:
                self.messages_widget.load_messages(chat_id)
                # 获取聊天成员信息并更新顶部信息栏
                self.refresh_chat_info(chat_id)
                # 更新当前聊天ID
                self.chat_info_bar.set_current_chat_id(chat_id)

    def show_chat_info(self):
        """显示群聊信息"""
        chat_id = self.chats_window.get_selected_chat_id()
        if chat_id:
            members = self.human_agent.get_chat_members(chat_id, True)
            online_members = self.human_agent.get_chat_online_members(chat_id)
            dialog = ChatInfoDialog(chat_id, members, online_members, self)
            # 连接成员变化信号
            dialog.members_changed.connect(self.refresh_chat_info)
            dialog.exec()

    def send_message(self, text: str):
        """发送消息"""
        chat_id = self.chats_window.get_selected_chat_id()
        if chat_id:
            self.human_agent.send_message(text, chat_id)

    def on_message_received(self, message):
        """处理接收到的消息"""
        current_chat_id = self.chats_window.get_selected_chat_id()
        if current_chat_id and message.chat_id == current_chat_id:
            # 如果是当前聊天的消息，添加到消息窗口
            self.messages_widget.add_message(message)
    
    def on_message_sent(self, message):
        """处理发送的消息"""
        current_chat_id = self.chats_window.get_selected_chat_id()
        if current_chat_id and message.chat_id == current_chat_id:
            # 如果是当前聊天的消息，添加到消息窗口
            self.messages_widget.add_message(message)

    def on_login_success(self):
        """登录成功后的处理"""
        self.setWindowTitle(f'聊天客户端 - {self.human_agent.name}')
