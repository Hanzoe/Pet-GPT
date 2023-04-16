from PyQt5.QtWidgets import QDialog, QVBoxLayout, QSizePolicy,\
    QTextEdit, QPushButton,  QHBoxLayout, QComboBox, QPlainTextEdit, QMainWindow,  QFrame, QDesktopWidget, QLabel,QWidget, QScrollArea, QGridLayout, QSpacerItem
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QEvent, QSize, QTimer
from .openai_api import OpenAI_API
from PyQt5.QtGui import QKeyEvent, QPixmap, QFontMetrics
import datetime
import os
import sys

class ChatWindow(QMainWindow):
    chat_window_closed = pyqtSignal()

    def __init__(self, parent=None,config="private_config.ini"):
        super().__init__(parent)

        self.setWindowTitle(f'与{config["Pet"]["NICKNAME"]}聊天')
        
         # 创建侧边栏
        side_bar = QVBoxLayout()
        side_bar.setAlignment(Qt.AlignTop)


        #在这里自定义常规按钮

        #新建常规按钮格式
        #xxxx_button = QPushButton("xxxx")
        #xxxx_button.clicked.connect(self.xxxx_slot)
        #side_bar.addWidget(xxxx_button)
        #之后去后面定义xxxx_slot

        english_button = QPushButton("英语润色")
        english_button.clicked.connect(self.english_button_slot)
        side_bar.addWidget(english_button)

        python_button = QPushButton("python编译器")
        python_button.clicked.connect(self.python_slot)
        side_bar.addWidget(python_button)

        text_adventure_button = QPushButton("文字冒险")
        text_adventure_button.clicked.connect(self.text_adventure)
        side_bar.addWidget(text_adventure_button)


        #在这里自定义下拉组件按钮

        #新建常规下拉组件格式
        #custom_dropdown.addItem("自定义选项 1")
        #xxxx_button.clicked.connect(self.xxxx_slot)
        #side_bar.addWidget(xxxx_button)
        #之后去后面定义xxxx_slot
        self.custom_dropdown = QComboBox()
        self.custom_dropdown.addItem("阅读理解PDF论文")
        self.custom_dropdown.addItem("自定义选项 2")
        self.custom_dropdown.addItem("自定义选项 3")
        self.custom_dropdown.addItem("自定义选项 4")
        side_bar.addWidget(self.custom_dropdown)
        
        total_button = QPushButton("执行下拉框按钮")
        total_button.clicked.connect(self.full_slot)
        side_bar.addWidget(total_button)

        #聊天主体
        self.chat_dialog_body = ChatDialogBody(config)
        
        # 将侧边栏和聊天主体结合
        main_layout = QHBoxLayout()
        sidebar_frame = QFrame()
        sidebar_frame.setLayout(side_bar)
        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.chat_dialog_body)

        main_widget = QFrame(self)
        self.setCentralWidget(main_widget)
        main_widget.setLayout(main_layout)


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

    # 为按钮添加事件-模板

    def example_slot(self):
        print("Button clicked")
    

    def english_button_slot(self):
        message = f'我想让你充当英语翻译，拼写校正者和改进者。我会用任何语言和你说话，你会检测到这种语言，翻译它，并用我的文本的更正和改进版本回答，用英语。我想让你用更漂亮优雅的高级英语单词和句子替换我的简化A0级单词和句子。保持意思不变，但使它们更具文学色彩。'+\
            '我想让你只回复更正，改进和没有其他东西，不要写解释。我的第一句话是“我希望明天更美好”'
        self.send_to_gpt(message)
        
    def python_slot(self):
        message = f'我希望你表现得像个Python解释器。我会给你Python代码，你会执行它。不要提供任何解释。'+\
            '除了代码的输出之外，不要使用任何东西进行响应。第一个代码是：“打印（‘你好世界！’）”'
        self.send_to_gpt(message)

    def text_adventure(self):
        message = f'现在来充当一个文字冒险游戏，描述时候注意节奏，不要太快，仔细描述各个人物的心情和周边环境。一次只需写四到六句话。主题等你回复后确定'+\
            '之后所有回答只需要一次续写四到六句话，总共就只讲5分钟内发生的事情。（直到我说结束）。理解之后：请回复“现在请你确定一个主题”'
        self.send_to_gpt(message)

    #通用函数
    def send_to_gpt(self,message):
        self.chat_dialog_body.add_message("system",message)
        # 更新聊天上下文
        self.chat_dialog_body.context_history += f"user: {message}\n"
        prompt = message
        self.chat_dialog_body.open_ai.prompt_queue.put((prompt, self.chat_dialog_body.context_history))  # 将聊天上下文作为第二个参数传递


    # 为下拉按钮创建槽函数-模板
    def full_slot(self):
        selected_item = self.custom_dropdown.currentText()
        if selected_item == "阅读理解PDF论文":
            self.function_1()
        elif selected_item == "自定义选项 2":
            self.function_2()
        elif selected_item == "自定义选项 3":
            self.function_3()
        elif selected_item == "自定义选项 4":
            self.function_4()

    def function_1(self):
        from .function.理解PDF文档内容 import 理解PDF文档内容标准文件输入
        理解PDF文档内容标准文件输入(self.chat_dialog_body)

    def function_2(self):
        print("我是2号")

    def function_3(self):
        print("我是3号")

    def function_4(self):
        print("我是4号")

#聊天框的主体部分
class ChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 只显示垂直滚动条
        
        self.container = QWidget(self.scroll_area)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)  # 设置控件之间的间距为 0
        
        self.scroll_area.setWidget(self.container)

        layout = QHBoxLayout(self)
        layout.addWidget(self.scroll_area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addSpacing(10)

    def clear_chat_history(self):
    # 清空布局中的所有组件
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


class MessageWidget(QWidget):
    def __init__(self, role, text, parent=None):
        super().__init__(parent)
        self.role = role
        self.text = text
        # 图像
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        avatar = QPixmap("image\\avatar_{}.png".format(role)).scaledToWidth(30).scaledToHeight(30)
        self.label.setPixmap(avatar)
        # 文字
        self.text_label = QLabel(self)
        self.text_label.setWordWrap(True)
        self.text_label.setText(text)
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # 设置大小策略
        # size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # size_policy.setHeightForWidth(True)
        # self.text_label.setSizePolicy(size_policy)
        
        # 使用 QGridLayout 布局来实现宽度比例的设置
        layout = QGridLayout(self)
        layout.addWidget(self.label, 0, 1, 2, 1, Qt.AlignTop)
        layout.addWidget(self.text_label, 0, 2, 1, 3, Qt.AlignTop)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Expanding), 0, 0, 1, 1)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Fixed), 0, 5, 1, 1)
        layout.setColumnStretch(2, 3)
        layout.setColumnStretch(3, 5)
        layout.setColumnMinimumWidth(4, 20)
        layout.setColumnStretch(5, 1)
        layout.setContentsMargins(0, 0, 0, 0)

        # 设置最大高度，使其与最小高度一致
        self.setMaximumHeight(self.sizeHint().height()) 

    def sizeHint(self):
        fm = QFontMetrics(self.text_label.font())
        text_width = self.text_label.sizeHint().width()
        text_height = fm.size(Qt.TextWordWrap, self.text_label.text()).height() + fm.descent() + 5
        return QSize(text_width + self.label.sizeHint().width() + 40, text_height + 20)



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

        self.chat_history = ChatWidget()
        layout.addWidget(self.chat_history)
        
        chat_input_layout = QHBoxLayout()
        self.message_input = QPlainTextEdit()
        self.message_input.setPlaceholderText("Send a message...")
        self.message_input.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.message_input.setFixedHeight(50)
        self.message_input.installEventFilter(self)
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

    # #用来区别身份的聊天记录
    # def append_message(self, message, is_user=False):
    #     """
    #     向聊天历史记录中添加消息，并设置不同颜色
    #     """
    #     color = "red" if is_user else "black"
    #     message = f"<font color='{color}'>{message}</font>"
    #     self.chat_history.insertHtml(message + "<br>")
    
    #窗口增加信息的统一模块
    def add_message(self,role,text):
        #封装成组件
        message=MessageWidget(role,text)
        self.chat_history.container_layout.addWidget(message)
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

    #按下发送按钮后的事件
    def send_message(self):
        text = self.message_input.toPlainText()
        role = "user"
        if text:
            self.add_message(role,text)
            # 更新聊天上下文
            self.context_history += f"user: {text}\n"
            # 将聊天上下文作为第二个参数传递给openai
            self.open_ai.prompt_queue.put((text, self.context_history))  
            # 清楚输入框
            self.message_input.clear()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ShiftModifier:
                self.message_input.insertPlainText("\n")
            else:
                self.send_message()
        else:
            super().keyPressEvent(event)

    def handle_response(self, response):
        if response and 'choices' in response:
            pet_reply = response['choices'][0]['message']['content'].strip().replace('\n', '').replace('\r', '')
            # 将 AI 回应添加到聊天上下文
            self.context_history += f"assistant: {pet_reply}\n"
        elif response and 'error' in response:
            pet_reply = f": 发生错误 - {response['error']}"
        else:
            pet_reply = ":对不起，我无法回应您的问题，请稍后再试。"
        self.add_message("pet",pet_reply)

    def save_chat_history(self,message):
        with open(self.chat_log_file, "w", encoding="utf-8") as f:
            f.write(message.text_label.text())
        print(f"聊天记录已保存到 {os.path.abspath(self.chat_log_file)}")

    
    def create_chat_log_file(self):
        chat_log_file = f"chat_history_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "log")

        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        self.chat_log_file = os.path.join(log_dir, chat_log_file)

    def clear_chat_history(self):
        # 清空聊天记录和聊天上下文
        self.chat_history.clear_chat_history()
        self.context_history = ""
        # 创建一个新的聊天记录文件
        self.create_chat_log_file()

    def closeEvent(self, event):
        self.save_chat_history()
        self.context_history = ""
        event.accept()

        # 发送 chat_window_closed 信号
        self.parent().chat_window_closed.emit()

