
from typing import List

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QHBoxLayout, QWidget, QPushButton,
                             QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer
from dto import Member
import globals


class SelectMembersDialog(QDialog):
    """选择成员对话框"""

    def __init__(self, online_members: list[Member], existing_members: list[str], parent=None):
        super().__init__(parent)
        self.online_members = online_members
        self.existing_members = existing_members
        self.selected_members = []
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("选择要拉入群的成员")
        layout = QVBoxLayout(self)

        # 成员列表
        self.members_list = QListWidget()
        self.members_list.setSelectionMode(QListWidget.MultiSelection)  # 允许多选

        # 添加在线成员（排除已在群内的）
        for member in self.online_members:
            if member.member_id not in self.existing_members:
                item = QListWidgetItem(f"{member.name}")
                item.setData(Qt.UserRole, member)  # 保存成员数据
                self.members_list.addItem(item)

        layout.addWidget(self.members_list)

        # 添加确定和取消按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.resize(300, 400)

    def get_selected_members(self) -> list[Member]:
        """获取选中的成员"""
        return [item.data(Qt.UserRole) for item in self.members_list.selectedItems()]


class ChatInfoDialog(QDialog):
    # 添加成员变化信号
    members_changed = Signal(str)  # 参数为chat_id
    
    def __init__(self, chat_id: str, members: list[Member], online_members: list[str], parent=None):
        super().__init__(parent)
        self.chat_id = chat_id
        self.members = members
        self.online_members = online_members
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        self.setWindowTitle("群聊信息")
        layout = QVBoxLayout(self)

        # 群聊ID
        id_layout = QHBoxLayout()
        id_label = QLabel("群聊ID:")
        id_label.setStyleSheet("font-weight: bold;")
        id_value = QLabel(self.chat_id)
        id_value.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 允许选择文本
        id_layout.addWidget(id_label)
        id_layout.addWidget(id_value)
        id_layout.addStretch()
        layout.addLayout(id_layout)

        # 成员列表标题
        self.members_title = QLabel(self)
        self.members_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(self.members_title)
        self.update_members_title()

        # 成员列表
        self.members_list = QListWidget(self)
        self.members_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #DDDDDD;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #E6F3FF;
            }
        """)

        for member in self.members:
            self.add_member_item(member)

        layout.addWidget(self.members_list)

        # 添加拉人入群按钮
        self.pull_button = QPushButton("+")
        self.pull_button.setStyleSheet("""
            QPushButton {
                background-color: #07C160;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #06AD56;
            }
        """)
        self.pull_button.clicked.connect(self.on_pull_button_clicked)
        layout.addWidget(self.pull_button)

        # 设置窗口大小
        self.resize(400, 500)

    def update_members_title(self):
        """更新成员列表标题"""
        self.members_title.setText(f"群成员 ({len(self.members)})")

    def setup_shortcuts(self):
        """设置快捷键"""
        self.members_list.keyPressEvent = self.on_key_press

    def on_key_press(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Delete:
            self.delete_selected_member()
        else:
            # 保持原有的键盘事件处理
            QListWidget.keyPressEvent(self.members_list, event)

    def delete_selected_member(self):
        """删除选中的成员"""
        current_item = self.members_list.currentItem()
        if not current_item:
            return

        member = current_item.data(Qt.UserRole)
        if not member:
            return

        # 显示确认对话框
        reply = QMessageBox.question(
            self,
            '确认删除',
            f'确定要将成员 {member.name} 移出群聊吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            human_agent = globals.get_human_agent()
            if human_agent:
                # 从群聊中移除成员
                success = human_agent.remove_member_from_chat(self.chat_id, member.member_id)
                if success:
                    print(f"成功移除成员: {member.name}")
                    # 延迟500ms后刷新，等待服务器处理
                    QTimer.singleShot(100, lambda: self.delayed_refresh())
                else:
                    QMessageBox.warning(self, '错误', '移除成员失败')

    def delayed_refresh(self):
        """延迟刷新"""
        human_agent = globals.get_human_agent()
        if human_agent:
            print("开始延迟刷新...")
            # 获取最新的成员列表
            self.members = human_agent.get_chat_members(self.chat_id, True)
            print(f"获取到的成员列表: {[m.name for m in self.members]}")
            # 获取最新的在线成员列表
            self.online_members = human_agent.get_chat_online_members(self.chat_id)
            print(f"获取到的在线成员: {self.online_members}")
            # 刷新成员列表
            self.refresh_members_list()
            # 发送成员变化信号
            self.members_changed.emit(self.chat_id)
            print("刷新完成")

    def add_member_item(self, member: Member):
        """添加成员项到列表"""
        item = QListWidgetItem()
        widget = QWidget(self)
        item_layout = QHBoxLayout(widget)

        # 成员名称
        name_label = QLabel(member.name)
        item_layout.addWidget(name_label)

        # 在线状态
        status_label = QLabel("在线" if member.member_id in self.online_members else "离线")
        status_label.setStyleSheet(f"""
            color: {'green' if member.member_id in self.online_members else 'gray'};
            margin-right: 10px;
        """)
        item_layout.addStretch()
        item_layout.addWidget(status_label)

        widget.setLayout(item_layout)
        item.setSizeHint(widget.sizeHint())
        # 保存成员数据
        item.setData(Qt.UserRole, member)
        self.members_list.addItem(item)
        self.members_list.setItemWidget(item, widget)

    def on_pull_button_clicked(self):
        """处理拉人入群按钮点击事件"""
        # 获取所有在线成员
        human_agent = globals.get_human_agent()
        if human_agent:
            online_member_ids: List[str] = human_agent.get_online_members()
            existing_member_ids = [m.member_id for m in self.members]
            online_members = human_agent.get_members(online_member_ids)

            # 创建选择成员对话框
            dialog = SelectMembersDialog(
                online_members=online_members,
                existing_members=existing_member_ids,
                parent=self
            )

            if dialog.exec() == QDialog.Accepted:
                selected_members = dialog.get_selected_members()
                if selected_members:
                    # 拉人入群
                    member_ids = [m.member_id for m in selected_members]
                    success = human_agent.pull_members_into_chat(self.chat_id, member_ids)
                    if success:
                        print("成功拉人入群，开始刷新...")
                        # 延迟100ms后刷新，等待服务器处理
                        QTimer.singleShot(100, lambda: self.delayed_refresh())
                    else:
                        QMessageBox.warning(self, '错误', '拉人入群失败')

    def refresh_members_list(self):
        """刷新成员列表"""
        # 清空列表
        self.members_list.clear()
        # 添加成员
        for member in self.members:
            self.add_member_item(member)
        # 更新标题
        self.update_members_title()
