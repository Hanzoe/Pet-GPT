from PyQt5.QtWidgets import QDialog, QVBoxLayout, QSizePolicy,\
    QTextEdit, QPushButton,  QHBoxLayout, QComboBox, QPlainTextEdit, QMainWindow,  QFrame, QDesktopWidget, QLabel,QWidget, QScrollArea, QGridLayout, QSpacerItem
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QEvent, QSize, QTimer
from .chat_function import ChatDialogBody

class ChatWindow(QMainWindow):
    def __init__(self, parent=None,config="private_config.ini"):
        super().__init__(parent)
        self.setWindowTitle(f'与{config["Pet"]["NICKNAME"]}聊天')
         # 创建侧边栏
        side_bar = QVBoxLayout()
        side_bar.setAlignment(Qt.AlignTop)
        self.config = config
        #你可以做的:在这里自定义常规按钮
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
        self.chat_dialog_body = ChatDialogBody(self.config)
        
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

        # 获取屏幕中心点chat_model/chat_main_windows.py
        screen = QDesktopWidget().screenGeometry()
        center = screen.center()

        # 将窗口移动到屏幕中心
        self.move(center - self.rect().center())
        # # 新增信号连接
        
        # # 隐藏宠物
        # parent.hide_pet()

    def closeEvent(self, event):
    # 关闭聊天窗口时，将宠物重新显示出来
        self.parent().show_pet()
        self.parent().toggle_chat_window()
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
        # 更新历史上下文
        self.chat_dialog_body.context_history[2].append(message)
        prompt = message
        self.chat_dialog_body.open_ai.prompt_queue.put((prompt, self.chat_dialog_body.context_history,message,False))  # 将聊天上下文作为第二个参数传递


    # 为下拉按钮创建槽函数-模板
    def full_slot(self):
        selected_item = self.custom_dropdown.currentText()
        if selected_item == "(开发中）阅读理解PDF论文":
            self.function_1()
        elif selected_item == "自定义选项 2":
            self.function_2()
        elif selected_item == "自定义选项 3":
            self.function_3()
        elif selected_item == "自定义选项 4":
            self.function_4()

    def function_1(self):
        from .function.function_PDFAnalyzer import PDFAnalyzer
        temple = PDFAnalyzer(self.chat_dialog_body,self.config)
        temple.main_pdf()

    def function_2(self):
        print("我是2号")

    def function_3(self):
        print("我是3号")

    def function_4(self):
        print("我是4号")