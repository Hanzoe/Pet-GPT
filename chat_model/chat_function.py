from PyQt5.QtWidgets import QDialog, QVBoxLayout, QSizePolicy,\
    QTextEdit, QPushButton,  QHBoxLayout, QComboBox, QPlainTextEdit, QMainWindow,  QFrame, QDesktopWidget, QLabel, QWidget, QScrollArea, QGridLayout, QSpacerItem
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QEvent, QSize, QTimer
from PyQt5.QtGui import QKeyEvent
import datetime
import os
import re
import time

import tiktoken
import numpy as np
from .openai_request import OpenAI_request
from .chat_windows import MessageWidget, ChatWidget

# 聊天的具体实现
class ChatDialogBody(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.config = config

        # 创建一个日志文件用于保存聊天记录
        self.create_chat_log_file()
        # 调用gpt接口
        self.open_ai = OpenAI_request(config)

        # 创建新线程发出http请求
        # 原来的线程则负责持续更新UI，实现一个超时倒计时，并等待新线程的任务完成
        # #多线程请求
        self.request_thread = QThread()
        self.request_thread.start()

        # 将 self.open_ai 移动到线程并启动
        self.open_ai.moveToThread(self.request_thread)
        self.open_ai.start()

        #请求中的组件
        self.system_message_index = -1

        # 创建变量以保存聊天上下文，注意user和gpt的对话轮流进入m，0是user，1是pet,3是system
        self.context_history = [[],[],[]]
        self.init_ui()

    def init_ui(self):
        # api的槽函数
        self.open_ai.response_received.connect(self.handle_response)
        # 总容器
        layout = QVBoxLayout()

        # 聊天记录部分
        self.chat_history = ChatWidget()
        layout.addWidget(self.chat_history)

        # 输入框
        chat_input_layout = QHBoxLayout()
        self.message_input = QPlainTextEdit()
        self.message_input.setPlaceholderText("Send a message...")
        self.message_input.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.message_input.setFixedHeight(50)
        self.message_input.installEventFilter(self)
        chat_input_layout.addWidget(self.message_input, stretch=2)

        # 发送按钮
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

    # 发送信息监听，使用回车发送
    def eventFilter(self, source, event):
        if source == self.message_input and event.type() == QEvent.KeyPress:
            key_event = QKeyEvent(event)
            if key_event.key() == Qt.Key_Return or key_event.key() == Qt.Key_Enter:
                if key_event.modifiers() & Qt.ShiftModifier:
                    self.message_input.insertPlainText("\n")
                else:
                    self.send_message()
                return True
        return super().eventFilter(source, event)

    # 聊天记录组件增加信息的统一模块
    def add_message(self, role, text):
        # 封装成组件
        message = MessageWidget(role, text)
        self.chat_history.container_layout.addWidget(message)
        # if role == "system":
        #     index = self.chat_history.container_layout.count()
        #     return index
        # 分割线
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.chat_history.container_layout.addWidget(line)  # 将分隔线添加到布局中
        # 强制更新容器的大小
        self.chat_history.container.adjustSize()
        # 滚动条到最下面
    
        def scroll():
            max_value = self.chat_history.scroll_area.verticalScrollBar().maximum()
            self.chat_history.scroll_area.verticalScrollBar().setValue(max_value)

        QTimer.singleShot(0, scroll)
        # 保存聊天记录到本地
        self.save_chat_history(message)
    
    def remove_message_at_index(self, index):
        if index < 0 or index >= self.chat_history.container_layout.count():
            return
        message_to_delete = self.chat_history.container_layout.takeAt(index)
        if message_to_delete.widget():
            message_to_delete.widget().setParent(None)
            message_to_delete.widget().deleteLater()

        separator_to_delete = self.chat_history.container_layout.takeAt(index)
        if separator_to_delete.widget():
            separator_to_delete.widget().setParent(None)
            separator_to_delete.widget().deleteLater()

    # 按下发送按钮后的事件
    def send_message(self):
        text = self.message_input.toPlainText()
        role = "user"
        if text:
            self.add_message(role, text)
            # 用户反馈
            #用来清除的代码
            # self.system_message_index = self.add_message("system", "请求中...")
            # self.add_message("system", "请求中...")
            # 更新聊天上下文
            self.context_history[0].append(text)
            # 将聊天上下文作为第二个参数传递给openai
            # 系统角色
            sys_prompt = "You are an AI language model."
            self.open_ai.prompt_queue.put((text, self.context_history, sys_prompt))
            # gpt_resp = self.get_response_from_gpt(text)
            # self.context_history += f"assistant: {gpt_resp}\n"
            # 清除输入框
            self.message_input.clear()

    # 监听键盘事件
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ShiftModifier:
                self.message_input.insertPlainText("\n")
            else:
                self.send_message()
        else:
            super().keyPressEvent(event)

    # 处理gpt的返回数据
    def handle_response(self, response):
        self.context_history[1].append(response)
        if self.system_message_index != -1:
            self.remove_message_at_index(self.system_message_index)
            self.system_message_index = -1
        self.add_message("pet", response)

    # 保存聊天记录
    def save_chat_history(self, message):
        with open(self.chat_log_file, "a", encoding="utf-8") as f:
            f.write(f"{message.role}: {message.text_label.text()}\n")
        print(f"聊天记录已保存到 {os.path.abspath(self.chat_log_file)}")

    # 创建log保存文件
    def create_chat_log_file(self):
        chat_log_file = f"chat_history_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        log_dir = os.path.join(os.path.abspath(
            os.path.dirname(__file__)), "log")

        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        self.chat_log_file = os.path.join(log_dir, chat_log_file)

    # 清除历史
    def clear_chat_history(self):
        # 清空聊天记录和聊天上下文
        self.chat_history.clear_chat_history()
        self.context_history = [[],[]]
        # 创建一个新的聊天记录文件
        self.create_chat_log_file()

    # 关闭按钮事件
    def closeEvent(self, event):
        self.context_history = [[],[]]
        event.accept()

        # 发送 chat_window_closed 信号
        self.parent().chat_window_closed.emit()

    # 减少当前请求
    def get_reduce_token_percent(self, text):
        """
            * 此函数未来将被弃用
        """
        try:
            # text = "maximum context length is 4097 tokens. However, your messages resulted in 4870 tokens"
            pattern = r"(\d+)\s+tokens\b"
            match = re.findall(pattern, text)
            EXCEED_ALLO = 500  # 稍微留一点余地，否则在回复时会因余量太少出问题
            max_limit = float(match[0]) - EXCEED_ALLO
            current_tokens = float(match[1])
            ratio = max_limit/current_tokens
            assert ratio > 0 and ratio < 1
            return ratio, str(int(current_tokens-max_limit))
        except:
            return 0.5, '不详'

    #命令过长时，进行剪切
    def input_clipping(self, inputs, history, max_token_limit):

        enc = tiktoken.encoding_for_model(self.config["OpenAI"]["LLM_MODEL"])

        def get_token_num(txt): return len(
            enc.encode(txt, disallowed_special=()))

        mode = 'input-and-history'
        # 当 输入部分的token占比 小于 全文的一半时，只裁剪历史
        input_token_num = get_token_num(inputs)
        if input_token_num < max_token_limit//2:
            mode = 'only-history'
            max_token_limit = max_token_limit - input_token_num

        everything = [inputs] if mode == 'input-and-history' else ['']
        everything.extend(history)
        n_token = get_token_num('\n'.join(everything))
        everything_token = [get_token_num(e) for e in everything]
        delta = max(everything_token) // 16  # 截断时的颗粒度

        while n_token > max_token_limit:
            where = np.argmax(everything_token)
            encoded = enc.encode(everything[where], disallowed_special=())
            clipped_encoded = encoded[:len(encoded)-delta]
            # -1 to remove the may-be illegal char
            everything[where] = enc.decode(clipped_encoded)[:-1]
            everything_token[where] = get_token_num(everything[where])
            n_token = get_token_num('\n'.join(everything))

        if mode == 'input-and-history':
            inputs = everything[0]
        else:
            pass
        history = everything[1:]
        return inputs, history



