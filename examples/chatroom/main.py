import sys
import os

# 获取原始模块所在的目录路径
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../client'))
sys.path.append(module_path)
from PySide6.QtWidgets import QApplication
from loginWindow import LoginWindow
from mainWindow import MainWindow

# print(os.path.abspath(module_path))


def main():
    app = QApplication(sys.argv)

    while True:
        # 创建并显示登录窗口
        login_window = LoginWindow()
        
        # 如果用户取消登录，则退出程序
        if login_window.exec() != LoginWindow.Accepted:
            break

        # 创建主窗口并显示
        try:
            main_window = MainWindow()
            main_window.show()
            return app.exec()
        except Exception as e:
            print(f"启动主窗口失败: {e}")
            continue

    sys.exit(0)


if __name__ == '__main__':
    main()
