"""
智校通2026 - 登录界面
技术栈: PyQt5 + SQLite + configparser + logging
"""
import sys
import sqlite3
import hashlib
import logging
import configparser
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout,
                             QButtonGroup, QMessageBox, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

# ---------- 日志配置 ----------
LOG_FILE = Path("app.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# ---------- 数据库初始化 ----------
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "user.db"


def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  role TEXT NOT NULL CHECK(role IN ('student','teacher','admin')))''')
    # 插入测试账号（密码: 123456）
    test_users = [
        ("test_stu", hashlib.sha256("123456".encode()).hexdigest(), "student"),
        ("test_tea", hashlib.sha256("123456".encode()).hexdigest(), "teacher"),
        ("test_admin", hashlib.sha256("123456".encode()).hexdigest(), "admin"),
    ]
    for user, pwd_hash, role in test_users:
        try:
            c.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                      (user, pwd_hash, role))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()


def check_login(username, password, role):
    """验证用户登录，返回 bool"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute("SELECT * FROM users WHERE username=? AND password_hash=? AND role=?",
                  (username, pwd_hash, role))
        result = c.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logging.error(f"数据库查询异常: {e}")
        return False


# ---------- 配置文件操作 ----------
CONFIG_FILE = Path("config.ini")
config = configparser.ConfigParser()


def load_config():
    if CONFIG_FILE.exists():
        config.read(str(CONFIG_FILE), encoding='utf-8')
    else:
        # 创建默认配置并写入文件
        config['LastLogin'] = {'username': '', 'role': 'student', 'remember': '0'}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)


def save_config(username, role, remember):
    config['LastLogin'] = {
        'username': username,
        'role': role,
        'remember': str(int(remember))
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        config.write(f)


# ---------- 主窗口占位 ----------
class MainWindow(QWidget):
    def __init__(self, role):
        super().__init__()
        self.setWindowTitle(f"智校通 - 主界面 ({role})")
        self.setFixedSize(800, 600)


# ---------- 登录窗口 ----------
class LoginWindow(QWidget):
    login_success = pyqtSignal(str)  # 发射角色

    def __init__(self):
        super().__init__()
        self.current_role = 'student'
        init_db()
        load_config()
        self.init_ui()
        self.load_last_config()
        self.set_stylesheet()

    def init_ui(self):
        self.setWindowTitle("智校通 EduSmart Hub - 登录")
        self.setFixedSize(450, 550)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # 标题区域
        self.logo_icon = QLabel("🎓")
        self.logo_icon.setAlignment(Qt.AlignCenter)
        self.logo_icon.setFont(QFont("Microsoft YaHei", 36))
        self.title_label = QLabel("智校通 EduSmart Hub")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        self.date_label = QLabel("2026年04月12日 · 星期日")
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("color: #64748b; font-size: 12px;")

        # 角色切换按钮组
        role_layout = QHBoxLayout()
        self.role_student_btn = QPushButton("学生")
        self.role_teacher_btn = QPushButton("教职工")
        self.role_admin_btn = QPushButton("管理员")
        self.role_btns = [self.role_student_btn, self.role_teacher_btn, self.role_admin_btn]
        for btn in self.role_btns:
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.setFont(QFont("Microsoft YaHei", 10))
            btn.clicked.connect(lambda _, b=btn: self.on_role_changed(b))
        self.role_student_btn.setChecked(True)  # 默认选中
        role_layout.addWidget(self.role_student_btn)
        role_layout.addWidget(self.role_teacher_btn)
        role_layout.addWidget(self.role_admin_btn)

        # 账号输入
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入您的账号")
        self.username_input.setFixedHeight(42)
        # 密码输入
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(42)
        self.password_input.returnPressed.connect(self.on_login)  # 回车触发

        # 记住我 & 忘记密码
        bottom_row = QHBoxLayout()
        self.remember_cb = QCheckBox("记住我")
        self.remember_cb.setFont(QFont("Microsoft YaHei", 9))
        self.forget_pwd_label = QLabel("<a href='#' style='color:#2563eb; text-decoration:none;'>忘记密码？</a>")
        self.forget_pwd_label.setFont(QFont("Microsoft YaHei", 9))
        self.forget_pwd_label.setCursor(Qt.PointingHandCursor)
        self.forget_pwd_label.linkActivated.connect(self.on_forget_pwd)
        bottom_row.addWidget(self.remember_cb)
        bottom_row.addStretch()
        bottom_row.addWidget(self.forget_pwd_label)

        # 登录按钮
        self.login_btn = QPushButton("立即进入系统  →")
        self.login_btn.setFixedHeight(44)
        self.login_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        self.login_btn.clicked.connect(self.on_login)

        # 错误提示
        self.msg_label = QLabel("")
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setStyleSheet("color: red; font-size: 12px;")
        self.msg_label.setVisible(False)

        # 社交登录按钮（装饰）
        social_layout = QHBoxLayout()
        self.wechat_btn = QPushButton("微信")
        self.dingtalk_btn = QPushButton("钉钉")
        self.github_btn = QPushButton("GitHub")
        for btn in [self.wechat_btn, self.dingtalk_btn, self.github_btn]:
            btn.setFixedSize(60, 60)
            btn.setStyleSheet("border-radius:30px; background:#f1f5f9; font-size:10px;")
            btn.setEnabled(False)  # 装饰用，不可点击
        social_layout.addStretch()
        social_layout.addWidget(self.wechat_btn)
        social_layout.addWidget(self.dingtalk_btn)
        social_layout.addWidget(self.github_btn)
        social_layout.addStretch()

        # 组装布局
        main_layout.addWidget(self.logo_icon)
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.date_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(role_layout)
        main_layout.addWidget(self.username_input)
        main_layout.addWidget(self.password_input)
        main_layout.addLayout(bottom_row)
        main_layout.addWidget(self.login_btn)
        main_layout.addWidget(self.msg_label)
        main_layout.addSpacing(20)
        main_layout.addLayout(social_layout)

        self.setLayout(main_layout)

    def set_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                font-family: "Microsoft YaHei";
            }
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 8px;
                background: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton {
                border-radius: 12px;
                background: #3b82f6;
                color: white;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QPushButton:checked {
                background: white;
                color: #3b82f6;
                border: 1px solid #ddd;
            }
            QCheckBox {
                font-size: 12px;
                color: #475569;
            }
        """)

    def load_last_config(self):
        last_user = config.get('LastLogin', 'username', fallback='')
        last_role = config.get('LastLogin', 'role', fallback='student')
        remember = config.getboolean('LastLogin', 'remember', fallback=False)
        if last_user:
            self.username_input.setText(last_user)
        self.remember_cb.setChecked(remember)
        # 设置角色按钮状态
        role_map = {'student': self.role_student_btn,
                    'teacher': self.role_teacher_btn,
                    'admin': self.role_admin_btn}
        for r, btn in role_map.items():
            btn.setChecked(r == last_role)
        self.current_role = last_role
        self.password_input.setFocus()

    def on_role_changed(self, btn):
        role_map = {
            self.role_student_btn: 'student',
            self.role_teacher_btn: 'teacher',
            self.role_admin_btn: 'admin'
        }
        self.current_role = role_map[btn]
        for b in self.role_btns:
            b.setChecked(b == btn)

    def on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            self.show_message("请输入账号和密码", "red")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("正在验证...")
        self.msg_label.setVisible(False)

        if check_login(username, password, self.current_role):
            logging.info(f"用户 {username} 登录成功，角色 {self.current_role}")
            if self.remember_cb.isChecked():
                save_config(username, self.current_role, True)
            else:
                save_config("", 'student', False)
            self.login_success.emit(self.current_role)
            self.close()
        else:
            logging.warning(f"登录失败：用户名 {username} 角色 {self.current_role}")
            self.show_message("账号或密码错误，请重试", "red")
            self.password_input.clear()
            self.password_input.setFocus()
            self.login_btn.setEnabled(True)
            self.login_btn.setText("立即进入系统  →")

    def show_message(self, text, color):
        self.msg_label.setText(text)
        self.msg_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        self.msg_label.setVisible(True)

    def on_forget_pwd(self):
        QMessageBox.information(self, "提示", "请联系管理员重置密码", QMessageBox.Ok)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    # 登录成功后打开主窗口（演示）
    def on_login_success(role):
        main = MainWindow(role)
        main.show()
        app.main_win = main  # 防止被回收
    login.login_success.connect(on_login_success)
    login.show()
    sys.exit(app.exec_())