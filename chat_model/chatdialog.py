from PyQt5.QtWidgets import QLabel, QDialog, QVBoxLayout, \
    QTextEdit, QPushButton, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QFrame, QApplication, QDesktopWidget
from .openai_api import OpenAI_API
from PyQt5.QtCore import QThread

class ChatWindow(QMainWindow):
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


class ChatDialogBody(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.config = config
        #调用gpt接口
        self.open_ai = OpenAI_API(config)
        self.init_ui()

        #多线程请求
        self.request_thread = QThread()
        self.request_thread.start()

        # 将 self.open_ai 移动到线程并启动
        self.open_ai.moveToThread(self.request_thread)
        self.open_ai.start()

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    #按下发送按钮后的事件
    def send_message(self):
        message = self.message_input.text()
        if message:
            self.chat_history.append("我: " + message)
            prompt = message
            self.open_ai.prompt_queue.put(prompt)
            self.message_input.clear()

    def handle_response(self, response, prompt):
        if response and 'choices' in response:
            pet_reply = self.open_ai.config["Pet"]["NICKNAME"] + response['choices'][0]['message']['content'].strip()
        elif response and 'error' in response:
            pet_reply = self.open_ai.config["Pet"]["NICKNAME"] + f": 发生错误 - {response['error']}"
        else:
            pet_reply = self.open_ai.config["Pet"]["NICKNAME"] + ":对不起，我无法回应您的问题，请稍后再试。"
        self.chat_history.append(pet_reply)
