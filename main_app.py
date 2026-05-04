"""
智校通 2026 - 主程序（集成知识库与 AI 服务）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # 确保能找到同级模块

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 导入页面类
from pages.home_page import HomePage
from pages.consult_page import ConsultPage
from pages.process_page import ProcessPage
from pages.knowledge_page import KnowledgePage
from pages.history_page import HistoryPage
from pages.profile_page import ProfilePage
from admin.review_page import ReviewPage

# 导入 AI 服务
from services.consult_service import ConsultService


class MainApp(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.role = role
        self.setWindowTitle("智校通 2026")
        self.setMinimumSize(1200, 800)

        # 从配置读取用户名
        self.username = self._get_username()

        # ---------- 初始化知识库 & AI 服务（主线程，避免子线程崩溃）----------
        self.consult_service = None
        try:
            # api_key 从环境变量 DEEPSEEK_API_KEY 读取；也可在这里直接写入字符串
            self.consult_service = ConsultService(api_key="sk-4f89bb00607f4646a8ca2cdd9c1e195b")
            # 如果知识库为空，则自动构建索引
            if self.consult_service.kb.collection_count() == 0:
                print("[Main] 正在构建知识库索引...")
                self.consult_service.kb.build_index(force_rebuild=True)
        except Exception as e:
            print(f"[Main] 知识库服务初始化失败: {e}")
            # 即使失败，程序仍可运行，只是咨询功能不可用

        self.init_ui()

    def _get_username(self):
        """从配置文件读取上次登录的用户名"""
        from login_window import config
        if config.has_section('LastLogin'):
            return config.get('LastLogin', 'username', fallback=self.role.capitalize())
        return self.role.capitalize()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- 左侧导航栏 ----
        nav_widget = QWidget()
        nav_widget.setFixedWidth(220)
        nav_widget.setStyleSheet("background-color: #1e293b; color: white;")
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(5)

        logo_label = QLabel("🎓 智校通")
        logo_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        logo_label.setStyleSheet("padding: 10px;")
        logo_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(logo_label)

        # 导航按钮配置 (显示文本, 内部键, 对应的页面类)
        self.nav_buttons = {}
        nav_items = [
            ("首页", "home", HomePage),
            ("智能咨询", "consult", ConsultPage),
            ("办事流程", "process", ProcessPage),
            ("知识库", "knowledge", KnowledgePage),
            ("历史记录", "history", HistoryPage),
            ("个人中心", "profile", ProfilePage),
        ]
        if self.role == 'admin':
            nav_items.insert(5, ("审核中心", "review", ReviewPage))

        for text, key, page_class in nav_items:
            btn = QPushButton(f"  {text}")
            btn.setCheckable(True)
            btn.setFont(QFont("Microsoft YaHei", 10))
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 12px 15px;
                    border-radius: 8px;
                    color: #cbd5e1;
                    background: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background: #334155;
                    color: white;
                }
                QPushButton:checked {
                    background: #3b82f6;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self.switch_page(k))
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        nav_layout.addStretch()

        user_info = QLabel(f"👤 {self.username}\n({self.role})")
        user_info.setStyleSheet("color: #94a3b8; padding: 10px;")
        user_info.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(user_info)

        logout_btn = QPushButton(" 退出登录")
        logout_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                border-radius: 8px;
                color: #f87171;
                background: transparent;
                border: none;
            }
            QPushButton:hover { background: #7f1d1d; }
        """)
        logout_btn.clicked.connect(self.logout)
        nav_layout.addWidget(logout_btn)

        nav_widget.setLayout(nav_layout)

        # ---- 右侧内容区域（QStackedWidget）----
        self.stack = QStackedWidget()
        self.pages = {}
        for _, key, page_class in nav_items:
            # 特殊处理咨询页面：传入已初始化好的服务
            if key == 'consult':
                page = ConsultPage(self.role, consult_service=self.consult_service)
            else:
                page = page_class(self.role)
            self.pages[key] = page
            self.stack.addWidget(page)

        main_layout.addWidget(nav_widget)
        main_layout.addWidget(self.stack, 1)

        central_widget.setLayout(main_layout)

        # 默认选中首页
        self.nav_buttons['home'].setChecked(True)
        self.stack.setCurrentWidget(self.pages['home'])

    def switch_page(self, key):
        for btn_key, btn in self.nav_buttons.items():
            btn.setChecked(btn_key == key)
        self.stack.setCurrentWidget(self.pages[key])

    def logout(self):
        from login_window import LoginWindow
        self.login_win = LoginWindow()
        self.login_win.login_success.connect(self.re_login)
        self.login_win.show()
        self.close()

    def re_login(self, role):
        self.new_main = MainApp(role)
        self.new_main.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 先显示登录窗口
    from login_window import LoginWindow
    login = LoginWindow()

    def start_main(role):
        main = MainApp(role)
        main.show()
        app.main_window = main  # 保持引用，防止被回收

    login.login_success.connect(start_main)
    login.show()

    sys.exit(app.exec_())