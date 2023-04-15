from PyQt5.QtWidgets import QLabel, QDialog, QVBoxLayout, \
    QTextEdit, QPushButton, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QFrame, QApplication, QDesktopWidget
from .openai_api import OpenAI_API
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QKeyEvent
import datetime
import os
from PyQt5.QtWidgets import QSplitter, QVBoxLayout, QPushButton, QComboBox

class ChatWindow(QMainWindow):
    chat_window_closed = pyqtSignal()

    def __init__(self, parent=None,config="private_config.ini"):
        super().__init__(parent)

        self.setWindowTitle(f'与{config["Pet"]["NICKNAME"]}聊天')
        
        #聊天主体
        chat_dialog_body = ChatDialogBody(config)

        main_widget = QFrame(self)
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(chat_dialog_body)

        # 设置窗口大小
        self.resize(800, 600)

        # 获取屏幕中心点
        screen = QDesktopWidget().screenGeometry()
        center = screen.center()

        # 将窗口移动到屏幕中心
        self.move(center - self.rect().center())
        # 新增信号连接
        self.chat_window_closed.connect(parent.show_pet)
        # 隐藏宠物
        parent.hide_pet()

    def closeEvent(self, event):
        # 关闭聊天窗口时，将宠物重新显示出来
        self.parent().show_pet()
        event.accept()

class ChatDialogBody(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.config = config

        # 创建一个日志文件用于保存聊天记录
        self.create_chat_log_file()
        #调用gpt接口
        self.open_ai = OpenAI_API(config)
        
        #多线程请求
        self.request_thread = QThread()
        self.request_thread.start()

        # 将 self.open_ai 移动到线程并启动
        self.open_ai.moveToThread(self.request_thread)
        self.open_ai.start()

        # 创建变量以保存聊天上下文
        self.context_history = ""
        self.init_ui()

    def init_ui(self):
        #api的槽函数
        self.open_ai.response_received.connect(self.handle_response)
        layout = QVBoxLayout()

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        chat_input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Send a message...")
        self.message_input.returnPressed.connect(self.send_message)
        chat_input_layout.addWidget(self.message_input, stretch=2)

        send_button = QPushButton('发送', self)
        send_button.clicked.connect(self.send_message)
        chat_input_layout.addWidget(send_button, stretch=1)

        
        # 添加清空聊天按钮
        clear_button = QPushButton('清空聊天', self)
        clear_button.clicked.connect(self.clear_chat_history)
        chat_input_layout.addWidget(clear_button, stretch=1)
        
        
        layout.addLayout(chat_input_layout)

        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F5;
                border-radius: 10px;
            }
            QTextEdit {
                background-color: white;
                color: black;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
        """)


    #用来区别身份的聊天记录
    def append_message(self, message, is_user=False):
        """
        向聊天历史记录中添加消息，并设置不同颜色
        """
        color = "red" if is_user else "black"
        message = f"<font color='{color}'>{message}</font>"
        self.chat_history.insertHtml(message + "<br>")
        
    #按下发送按钮后的事件
    def send_message(self):
        message = self.message_input.text()
        if message:
            self.append_message(message=f'我:{message}',is_user=True)
            # 更新聊天上下文
            self.context_history += f"user: {message}\n"
            prompt = message
            self.open_ai.prompt_queue.put((prompt, self.context_history))  # 将聊天上下文作为第二个参数传递
            self.message_input.clear()

            # 保存聊天记录到本地
            self.save_chat_history()

    def handle_response(self, response, prompt):
        if response and 'choices' in response:
            pet_reply = self.open_ai.config["Pet"]["NICKNAME"] + ":" + response['choices'][0]['message']['content'].strip().replace('\n', '').replace('\r', '')
            # 将 AI 回应添加到聊天上下文
            self.context_history += f"assistant: {pet_reply}\n"
        elif response and 'error' in response:
            pet_reply = self.open_ai.config["Pet"]["NICKNAME"] + f": 发生错误 - {response['error']}"
        else:
            pet_reply = self.open_ai.config["Pet"]["NICKNAME"] + ":对不起，我无法回应您的问题，请稍后再试。"
        self.append_message(message=pet_reply)
        # 保存聊天记录到本地
        self.save_chat_history()

    def save_chat_history(self):
        with open(self.chat_log_file, "a", encoding="utf-8") as f:
            f.write(self.chat_history.toPlainText())
        print(f"聊天记录已保存到 {os.path.abspath(self.chat_log_file)}")

    
    def create_chat_log_file(self):
        chat_log_file = f"chat_history_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "log")

        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        self.chat_log_file = os.path.join(log_dir, chat_log_file)

    def clear_chat_history(self):
        # 保存当前聊天记录
        self.save_chat_history()
        # 清空聊天记录和聊天上下文
        self.chat_history.clear()
        self.context_history = ""
        # 创建一个新的聊天记录文件
        self.create_chat_log_file()

    def closeEvent(self, event):
        self.save_chat_history()
        self.context_history = ""
        event.accept()

    def closeEvent(self, event):
        self.save_chat_history()
        self.context_history = ""
        event.accept()

        # 发送 chat_window_closed 信号
        self.parent().chat_window_closed.emit()

