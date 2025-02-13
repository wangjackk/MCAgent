from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QPushButton, 
                            QHBoxLayout, QMessageBox, QInputDialog)
from globals import get_human_agent

class JoinedChatsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.human_agent = get_human_agent()
        self.chats_list = QListWidget()
        self.chat_id_map = {}  # 保存名称到ID的映射
        
        # 创建按钮
        self.refresh_button = QPushButton('刷新')
        self.join_chat_button = QPushButton('加入聊天')
        self.create_chat_button = QPushButton('创建聊天')
        
        # 绑定按钮事件
        self.refresh_button.clicked.connect(self.refresh_chats)
        self.join_chat_button.clicked.connect(self.join_chat)
        self.create_chat_button.clicked.connect(self.create_chat)
        
        # 创建布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.join_chat_button)
        button_layout.addWidget(self.create_chat_button)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.chats_list)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        self.initUI()
        
        # 初始加载聊天室列表
        # self.refresh_chats()
        
        # 添加双击事件处理
        self.chats_list.itemDoubleClicked.connect(self.on_chat_double_clicked)

    def initUI(self):
        self.setWindowTitle('聊天列表')
        self.resize(350, 600)

    def refresh_chats(self):
        """刷新聊天室列表"""
        self.chats_list.clear()
        self.chat_id_map.clear()  # 清空映射
        joined_chats = self.human_agent.get_joined_chats()
        
        for chat_id in joined_chats:
            chat = self.human_agent.get_chat(chat_id)
            if chat:
                item_text = chat.name
                self.chats_list.addItem(item_text)
                self.chat_id_map[item_text] = chat_id  # 保存映射关系

    def join_chat(self):
        """加入新的聊天室"""
        chat_id, ok = QInputDialog.getText(
            self, '加入聊天室', '请输入聊天室ID:')
        
        if ok and chat_id:
            success, response = self.human_agent.join_chat(chat_id)
            if success:
                QMessageBox.information(self, '成功', '成功加入聊天室!')
                self.refresh_chats()
            else:
                QMessageBox.warning(self, '错误', f'加入失败: {response}')

    def create_chat(self):
        """创建新的聊天室"""
        chat_name, ok = QInputDialog.getText(
            self, '创建聊天室', '请输入聊天室名称:')
        
        if ok and chat_name:
            success, result = self.human_agent.create_chat(
                name=chat_name,
                description=f"Created by {self.human_agent.name}",
                join=True  # 创建后自动加入
            )
            
            if success:
                QMessageBox.information(self, '成功', '聊天室创建成功!')
                self.refresh_chats()
            else:
                QMessageBox.warning(self, '错误', f'创建失败: {result}')

    def get_selected_chat_id(self) -> str:
        """获取当前选中的聊天室ID"""
        current_item = self.chats_list.currentItem()
        if current_item:
            return self.chat_id_map.get(current_item.text())
        return None
    
    # show时刷新聊天室列表
    def showEvent(self, event):
        self.refresh_chats()
        super().showEvent(event)

    def on_chat_double_clicked(self, item):
        """处理聊天项的双击事件"""
        chat_id = self.get_selected_chat_id()
        if chat_id:
            # 这里可以添加双击处理逻辑
            pass
