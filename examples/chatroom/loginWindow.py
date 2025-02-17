import time

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                            QLineEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
import json
import os

from qtHumanAgent import QtHumanAgent
from globals import init_human_agent


class LoginWindow(QDialog):
    """登录窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = ""
        self.member_id = ""
        self.setup_ui()
        self.load_login_info()
    
    def setup_ui(self):
        """初始化UI"""
        self.setWindowTitle('登录')
        layout = QVBoxLayout(self)
        layout.setSpacing(20)  # 增加控件之间的间距
        layout.setContentsMargins(30, 30, 30, 30)  # 增加边距
        
        # 标题
        title = QLabel("聊天客户端")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 20px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 成员ID输入框
        id_label = QLabel("成员ID")
        id_label.setStyleSheet("font-size: 16px; color: #333333;")
        layout.addWidget(id_label)
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText('请输入成员ID')
        self.id_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #DDDDDD;
                border-radius: 6px;
                font-size: 16px;
                margin-bottom: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #07C160;
            }
        """)
        layout.addWidget(self.id_input)
        
        # 姓名输入框
        name_label = QLabel("姓名")
        name_label.setStyleSheet("font-size: 16px; color: #333333;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('请输入姓名')
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #DDDDDD;
                border-radius: 6px;
                font-size: 16px;
                margin-bottom: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #07C160;
            }
        """)
        layout.addWidget(self.name_input)
        
        # 登录按钮
        self.login_button = QPushButton('登录')
        self.login_button.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background-color: #07C160;
                color: white;
                border: none;
                border-radius: 6px;
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
        self.login_button.clicked.connect(self.on_login)
        layout.addWidget(self.login_button)
        
        # 添加注册按钮
        self.signup_button = QPushButton('注册')
        self.signup_button.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2868A9;
            }
        """)
        self.signup_button.clicked.connect(self.on_signup)
        layout.addWidget(self.signup_button)
        
        # 设置窗口属性
        self.setFixedSize(400, 500)  # 增大窗口尺寸
        self.setWindowFlags(Qt.WindowCloseButtonHint)  # 只显示关闭按钮
    
    def on_login(self):
        """处理登录按钮点击事件"""
        member_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        
        if not member_id or not name:
            QMessageBox.warning(self, '提示', '请输入成员ID和姓名')
            return
        
        human_agent: QtHumanAgent = init_human_agent(name, member_id)
        
        # 禁用登录按钮，避免重复点击
        self.login_button.setEnabled(False)
        self.login_button.setText('登录中...')
        
        try:
            success = human_agent.login()
            
            # 等待登录成功标志，最多等待5秒
            wait_time = 0
            while not human_agent.login_success and wait_time < 50:
                time.sleep(0.1)
                wait_time += 1
            
            if not human_agent.login_success:
                QMessageBox.warning(self, '错误', '登录失败，请检查成员ID是否正确')
                return
            
            self.member_id = member_id
            self.name = name
            
            self.save_login_info()
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, '错误', f'登录时发生错误：{str(e)}')
        finally:
            # 恢复登录按钮状态
            self.login_button.setEnabled(True)
            self.login_button.setText('登录')
    
    def on_signup(self):
        """处理注册按钮点击事件"""
        member_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        
        if not member_id or not name:
            QMessageBox.warning(self, '提示', '请输入成员ID和姓名')
            return
        
        human_agent = init_human_agent(name, member_id)
        result = human_agent.signup()

        print('signup result:', result)
        
        if result.get('status') in [200, 201]:
            QMessageBox.information(self, '成功', '注册成功！')
        else:
            QMessageBox.warning(self, '错误', f'注册失败：{result.get("message", "未知错误")}')
    
    def get_member_id(self) -> str:
        """获取成员ID"""
        return self.member_id
    
    def get_name(self) -> str:
        """获取姓名"""
        return self.name
    
    def load_login_info(self):
        """加载上次登录信息"""
        try:
            if os.path.exists('login_info.json'):
                with open('login_info.json', 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    self.id_input.setText(info.get('member_id', ''))
                    self.name_input.setText(info.get('name', ''))
        except Exception as e:
            print(f"加载登录信息失败: {e}")
    
    def save_login_info(self):
        """保存登录信息"""
        try:
            with open('login_info.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'member_id': self.member_id,
                    'name': self.name
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存登录信息失败: {e}")
