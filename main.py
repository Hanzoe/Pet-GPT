import os; os.environ['no_proxy'] = '*' # 避免代理网络产生意外污染

def main():
    import gradio as gr
    from request_llm.bridge_all import predict
    from toolbox import format_io, find_free_port, on_file_uploaded, on_report_generated, get_conf, ArgsGeneralWrapper, DummyWith
    # 建议您复制一个config_private.py放自己的秘密, 如API和代理网址, 避免不小心传github被别人看到
    proxies, WEB_PORT, LLM_MODEL, CONCURRENT_COUNT, AUTHENTICATION, CHATBOT_HEIGHT, LAYOUT, API_KEY, AVAIL_LLM_MODELS = \
        get_conf('proxies', 'WEB_PORT', 'LLM_MODEL', 'CONCURRENT_COUNT', 'AUTHENTICATION', 'CHATBOT_HEIGHT', 'LAYOUT', 'API_KEY', 'AVAIL_LLM_MODELS')

    # 如果WEB_PORT是-1, 则随机选取WEB端口
    PORT = find_free_port() if WEB_PORT <= 0 else WEB_PORT
    if not AUTHENTICATION: AUTHENTICATION = None

    from check_proxy import get_current_version
    initial_prompt = "Serve me as a writing and programming assistant."
    title_html = f"<h1 align=\"center\">ChatGPT 学术优化 {get_current_version()}</h1>"
    description =  """代码开源和更新[地址🚀](https://github.com/binary-husky/chatgpt_academic)，感谢热情的[开发者们❤️](https://github.com/binary-husky/chatgpt_academic/graphs/contributors)"""

    # 问询记录, python 版本建议3.9+（越新越好）
    import logging
    os.makedirs("gpt_log", exist_ok=True)
    try:logging.basicConfig(filename="gpt_log/chat_secrets.log", level=logging.INFO, encoding="utf-8")
    except:logging.basicConfig(filename="gpt_log/chat_secrets.log", level=logging.INFO)
    print("所有问询记录将自动保存在本地目录./gpt_log/chat_secrets.log, 请注意自我隐私保护哦！")

    # 一些普通功能模块
    from core_functional import get_core_functions
    functional = get_core_functions()

    # 高级函数插件
    from crazy_functional import get_crazy_functions
    crazy_fns = get_crazy_functions()

    # 处理markdown文本格式的转变
    gr.Chatbot.postprocess = format_io

    # 做一些外观色彩上的调整
    from theme import adjust_theme, advanced_css
    set_theme = adjust_theme()

    # 代理与自动更新
    from check_proxy import check_proxy, auto_update, warm_up_modules
    proxy_info = check_proxy(proxies)

    gr_L1 = lambda: gr.Row().style()
    gr_L2 = lambda scale: gr.Column(scale=scale)
    if LAYOUT == "TOP-DOWN": 
        gr_L1 = lambda: DummyWith()
        gr_L2 = lambda scale: gr.Row()
        CHATBOT_HEIGHT /= 2

    cancel_handles = []
    with gr.Blocks(title="ChatGPT 学术优化", theme=set_theme, analytics_enabled=False, css=advanced_css) as demo:
        gr.HTML(title_html)
        cookies = gr.State({'api_key': API_KEY, 'llm_model': LLM_MODEL})
        with gr_L1():
            with gr_L2(scale=2):
                chatbot = gr.Chatbot()
                chatbot.style(height=CHATBOT_HEIGHT)
                history = gr.State([])
            with gr_L2(scale=1):
                with gr.Accordion("输入区", open=True) as area_input_primary:
                    with gr.Row():
                        txt = gr.Textbox(show_label=False, placeholder="Input question here.").style(container=False)
                    with gr.Row():
                        submitBtn = gr.Button("提交", variant="primary")
                    with gr.Row():
                        resetBtn = gr.Button("重置", variant="secondary"); resetBtn.style(size="sm")
                        stopBtn = gr.Button("停止", variant="secondary"); stopBtn.style(size="sm")
                        clearBtn = gr.Button("清除", variant="secondary", visible=False); clearBtn.style(size="sm")
                    with gr.Row():
                        status = gr.Markdown(f"Tip: 按Enter提交, 按Shift+Enter换行。当前模型: {LLM_MODEL} \n {proxy_info}")
                with gr.Accordion("基础功能区", open=True) as area_basic_fn:
                    with gr.Row():
                        for k in functional:
                            variant = functional[k]["Color"] if "Color" in functional[k] else "secondary"
                            functional[k]["Button"] = gr.Button(k, variant=variant)
                with gr.Accordion("函数插件区", open=True) as area_crazy_fn:
                    with gr.Row():
                        gr.Markdown("注意：以下“红颜色”标识的函数插件需从输入区读取路径作为参数.")
                    with gr.Row():
                        for k in crazy_fns:
                            if not crazy_fns[k].get("AsButton", True): continue
                            variant = crazy_fns[k]["Color"] if "Color" in crazy_fns[k] else "secondary"
                            crazy_fns[k]["Button"] = gr.Button(k, variant=variant)
                            crazy_fns[k]["Button"].style(size="sm")
                    with gr.Row():
                        with gr.Accordion("更多函数插件", open=True):
                            dropdown_fn_list = [k for k in crazy_fns.keys() if not crazy_fns[k].get("AsButton", True)]
                            with gr.Column(scale=1):
                                dropdown = gr.Dropdown(dropdown_fn_list, value=r"打开插件列表", label="").style(container=False)
                            with gr.Column(scale=1):
                                switchy_bt = gr.Button(r"请先从插件列表中选择", variant="secondary")
                    with gr.Row():
                        with gr.Accordion("点击展开“文件上传区”。上传本地文件可供红色函数插件调用。", open=False) as area_file_up:
                            file_upload = gr.Files(label="任何文件, 但推荐上传压缩文件(zip, tar)", file_count="multiple")
                with gr.Accordion("更换模型 & SysPrompt & 交互界面布局", open=(LAYOUT == "TOP-DOWN")):
                    system_prompt = gr.Textbox(show_label=True, placeholder=f"System Prompt", label="System prompt", value=initial_prompt)
                    top_p = gr.Slider(minimum=-0, maximum=1.0, value=1.0, step=0.01,interactive=True, label="Top-p (nucleus sampling)",)
                    temperature = gr.Slider(minimum=-0, maximum=2.0, value=1.0, step=0.01, interactive=True, label="Temperature",)
                    max_length_sl = gr.Slider(minimum=256, maximum=4096, value=512, step=1, interactive=True, label="Local LLM MaxLength",)
                    checkboxes = gr.CheckboxGroup(["基础功能区", "函数插件区", "底部输入区", "输入清除键"], value=["基础功能区", "函数插件区"], label="显示/隐藏功能区")
                    md_dropdown = gr.Dropdown(AVAIL_LLM_MODELS, value=LLM_MODEL, label="更换LLM模型/请求源").style(container=False)

                    gr.Markdown(description)
                with gr.Accordion("备选输入区", open=True, visible=False) as area_input_secondary:
                    with gr.Row():
                        txt2 = gr.Textbox(show_label=False, placeholder="Input question here.", label="输入区2").style(container=False)
                    with gr.Row():
                        submitBtn2 = gr.Button("提交", variant="primary")
                    with gr.Row():
                        resetBtn2 = gr.Button("重置", variant="secondary"); resetBtn2.style(size="sm")
                        stopBtn2 = gr.Button("停止", variant="secondary"); stopBtn2.style(size="sm")
                        clearBtn2 = gr.Button("清除", variant="secondary", visible=False); clearBtn.style(size="sm")
        # 功能区显示开关与功能区的互动
        def fn_area_visibility(a):
            ret = {}
            ret.update({area_basic_fn: gr.update(visible=("基础功能区" in a))})
            ret.update({area_crazy_fn: gr.update(visible=("函数插件区" in a))})
            ret.update({area_input_primary: gr.update(visible=("底部输入区" not in a))})
            ret.update({area_input_secondary: gr.update(visible=("底部输入区" in a))})
            ret.update({clearBtn: gr.update(visible=("输入清除键" in a))})
            ret.update({clearBtn2: gr.update(visible=("输入清除键" in a))})
            if "底部输入区" in a: ret.update({txt: gr.update(value="")})
            return ret
        checkboxes.select(fn_area_visibility, [checkboxes], [area_basic_fn, area_crazy_fn, area_input_primary, area_input_secondary, txt, txt2, clearBtn, clearBtn2] )
        # 整理反复出现的控件句柄组合
        input_combo = [cookies, max_length_sl, md_dropdown, txt, txt2, top_p, temperature, chatbot, history, system_prompt]
        output_combo = [cookies, chatbot, history, status]
        predict_args = dict(fn=ArgsGeneralWrapper(predict), inputs=input_combo, outputs=output_combo)
        # 提交按钮、重置按钮
        cancel_handles.append(txt.submit(**predict_args))
        cancel_handles.append(txt2.submit(**predict_args))
        cancel_handles.append(submitBtn.click(**predict_args))
        cancel_handles.append(submitBtn2.click(**predict_args))
        resetBtn.click(lambda: ([], [], "已重置"), None, [chatbot, history, status])
        resetBtn2.click(lambda: ([], [], "已重置"), None, [chatbot, history, status])
        clearBtn.click(lambda: ("",""), None, [txt, txt2])
        clearBtn2.click(lambda: ("",""), None, [txt, txt2])
        # 基础功能区的回调函数注册
        for k in functional:
            click_handle = functional[k]["Button"].click(fn=ArgsGeneralWrapper(predict), inputs=[*input_combo, gr.State(True), gr.State(k)], outputs=output_combo)
            cancel_handles.append(click_handle)
        # 文件上传区，接收文件后与chatbot的互动
        file_upload.upload(on_file_uploaded, [file_upload, chatbot, txt, txt2, checkboxes], [chatbot, txt, txt2])
        # 函数插件-固定按钮区
        for k in crazy_fns:
            if not crazy_fns[k].get("AsButton", True): continue
            click_handle = crazy_fns[k]["Button"].click(ArgsGeneralWrapper(crazy_fns[k]["Function"]), [*input_combo, gr.State(PORT)], output_combo)
            click_handle.then(on_report_generated, [file_upload, chatbot], [file_upload, chatbot])
            cancel_handles.append(click_handle)
        # 函数插件-下拉菜单与随变按钮的互动
        def on_dropdown_changed(k):
            variant = crazy_fns[k]["Color"] if "Color" in crazy_fns[k] else "secondary"
            return {switchy_bt: gr.update(value=k, variant=variant)}
        dropdown.select(on_dropdown_changed, [dropdown], [switchy_bt] )
        # 随变按钮的回调函数注册
        def route(k, *args, **kwargs):
            if k in [r"打开插件列表", r"请先从插件列表中选择"]: return 
            yield from ArgsGeneralWrapper(crazy_fns[k]["Function"])(*args, **kwargs)
        click_handle = switchy_bt.click(route,[switchy_bt, *input_combo, gr.State(PORT)], output_combo)
        click_handle.then(on_report_generated, [file_upload, chatbot], [file_upload, chatbot])
        # def expand_file_area(file_upload, area_file_up):
        #     if len(file_upload)>0: return {area_file_up: gr.update(open=True)}
        # click_handle.then(expand_file_area, [file_upload, area_file_up], [area_file_up])
        cancel_handles.append(click_handle)
        # 终止按钮的回调函数注册
        stopBtn.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)
        stopBtn2.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)

    # gradio的inbrowser触发不太稳定，回滚代码到原始的浏览器打开函数
    def auto_opentab_delay():
        import threading, webbrowser, time
        print(f"如果浏览器没有自动打开，请复制并转到以下URL：")
        print(f"\t（亮色主题）: http://localhost:{PORT}")
        print(f"\t（暗色主题）: http://localhost:{PORT}/?__dark-theme=true")
        def open(): 
            time.sleep(2)       # 打开浏览器
            webbrowser.open_new_tab(f"http://localhost:{PORT}/?__dark-theme=true")
        threading.Thread(target=open, name="open-browser", daemon=True).start()
        threading.Thread(target=auto_update, name="self-upgrade", daemon=True).start()
        threading.Thread(target=warm_up_modules, name="warm-up", daemon=True).start()

    
    #桌面宠物的类
    #导入桌宠界面
    import sys
    from PyQt5.QtCore import Qt, QPoint, QTimer, QSize, QObject
    from PyQt5.QtGui import  QMovie, QKeySequence
    from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QLabel, QGraphicsDropShadowEffect, QFileDialog, QDialog, QVBoxLayout, \
        QPushButton, QLineEdit, QHBoxLayout, QInputDialog, QDesktopWidget, QCheckBox, QKeySequenceEdit
    import configparser
    import random
    import codecs
    from chat_model.chat_main_windows import ChatWindow
    import configparser
    #全局快捷键
    import keyboard
    import threading
    class DesktopPet(QWidget, QObject):
        def __init__(self, config):
            super().__init__()
            self.config = config
            self.init_ui()

            self.chat_window_state_changed = False

            # 监听全局快捷键的线程
            keyboard_listener_thread = threading.Thread(target=self._run_keyboard_listener, daemon=True)
            keyboard_listener_thread.start()
            # pet自由移动
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_position)
            self.toggle_walk(self.config.getboolean("Pet", "RANDOM_WALK"))

            # 获取最大屏幕
            desktop = QDesktopWidget().availableGeometry()
            self.max_x = desktop.width() - self.width()
            self.max_y = desktop.height() - self.height()

            self.direction = random.choice([-1, 1])  # 初始化移动方向
            # 停止和移动判断
            self.stop_timer = QTimer()
            self.stop_timer.timeout.connect(self.restart_movement)
            self.movement_timer = QTimer()
            self.movement_timer.timeout.connect(self.stop_movement)
            
            # 根据配置设置是否随机提问
            if self.config.getboolean("Pet", "RANDOM_CHAT"):
                self.set_new_timers()  # 初始化停止时间和移动时间
            #快捷键监听
            self.chat_window_open = False
            # web监听
            self.chat_web_thread = None


        #初始化界面
        def init_ui(self):
            #父容器
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.pet_width = self.config.getint("Pet", "WIDTH")
            self.pet_height = self.config.getint("Pet", "HEIGHT")
            self.setFixedSize(self.pet_width+20,self.pet_height+20)
            screen_geometry = QApplication.desktop().availableGeometry()
            self.move(screen_geometry.width() - self.width()-500, screen_geometry.height() - self.height()-100)

            #宠物信息
            self.pet_movie = QMovie(self.config["Pet"]["PET_ICON"])
            self.pet_movie.setScaledSize(QSize(self.pet_width, self.pet_height))
            self.pet_label = QLabel(self)
            self.pet_label.setMovie(self.pet_movie)
            self.pet_movie.start()
            self.nickname = self.config["Pet"]["NICKNAME"]

            # 创建一个布局管理器
            layout = QVBoxLayout(self)
            # 将 QLabel 添加到布局管理器中
            layout.addWidget(self.pet_label)
            # 设置布局管理器中的对齐方式，以让 QLabel 在中心显示
            layout.setAlignment(Qt.AlignCenter)
            # 将布局管理器设置为父容器的布局
            self.setLayout(layout)
            
            #右键功能区，可以自定义（擅长的朋友）
            self.menu = QMenu(self)
            #调用gpt聊天框
            chat_action = QAction("(开发中）本地聊天", self, triggered=self.toggle_chat_window)
            #调用web学术优化聊天框
            web_action = QAction("学术优化", self, triggered=self.toggle_chat_web)
            change_icon_action = QAction("更换图标", self, triggered=self.change_icon)
            exit_action = QAction("退出", self, triggered=self.close)
            change_nickname_action = QAction("改昵称", self, triggered=self.change_nickname)
            settings_action = QAction("设置", self, triggered=self.show_settings_dialog)
            self.menu.addActions([chat_action, web_action, change_icon_action, change_nickname_action, settings_action, exit_action])

            #随机发起对话功能的气泡框
            self.bubble = QLabel(self.parent())
            self.bubble.setWindowFlags(Qt.SplashScreen)
            pet_width = self.pet_width
            pet_height = self.pet_height
            self.bubble.setGeometry(pet_width, -60, 200, 50)
            self.bubble.setStyleSheet("background-color: white; border-radius: 10px; padding: 5px;")
            self.bubble.hide()

            shadow_effect = QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2)
            self.bubble.setGraphicsEffect(shadow_effect)
            self.show()

        # 快捷键启动窗口
        def toggle_chat_window(self):
            if self.chat_window_open:
                self.chat_window.close()
                self.chat_window_open = False
                self.chat_window = None
                self.chat_window_state_changed = True
            else:
                self.chat_window = ChatWindow(self, self.config)
                self.chat_window.show()
                self.chat_window_open = True
                self.chat_window_state_changed = True

        #修改昵称
        def change_nickname(self):
            new_nickname, ok = QInputDialog.getText(self, "改昵称", "请输入新的昵称：", QLineEdit.Normal, self.nickname)
            if ok and new_nickname != '':
                self.nickname = new_nickname
                # 修改配置项
                self.config.set('Pet', 'NICKNAME', new_nickname)
                # 保存修改后的配置文件
                self.save_config()
        
        #根据鼠标更新对话框位置
        def update_chat_dialog_position(self):
            if hasattr(self, 'chat_dialog') and self.chat_dialog.isVisible():
                dialog_position = self.mapToGlobal(QPoint(self.pet_pixmap.width() // 2, -self.chat_dialog.height()))
                self.chat_dialog.move(dialog_position)

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event):
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.drag_position)
                self.update_chat_dialog_position()

        def contextMenuEvent(self, event):
            self.menu.exec_(event.globalPos())

        # 修改图标路径
        def change_icon(self):
            # 请在此处添加选择图标的逻辑，可以使用 QFileDialog 获取文件路径
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            new_icon_path, _ = QFileDialog.getOpenFileName(self, "选择新图标", "", "Images (*.png *.xpm *.jpg *.bmp, *.gif);;All Files (*)", options=options)
            if new_icon_path:
                self.pet_movie.stop()  # 停止动画
                # 替换影片
                self.pet_movie.setFileName(new_icon_path)
                # 获取图片尺寸
                self.pet_movie.setScaledSize(QSize(self.pet_width, self.pet_height))
                # 开始播放影片
                self.pet_movie.start()
                # 修改配置项
                self.config.set('Pet', 'PET_ICON', new_icon_path)
                # 保存修改后的配置文件
                self.save_config()

        def set_new_timers(self):
            stop_time = random.randint(10000, 20000)  # 生成一个2~5秒的随机数，作为移动时间
            self.stop_timer.start(stop_time)

            movement_time = random.randint(10000, 20000)  # 生成一个2~5秒的随机数，作为移动时间
            self.movement_timer.start(movement_time)

            # 如果停止时间到了，则展示一句话
            QTimer.singleShot(stop_time, self.random_speak)

        def restart_movement(self):
            self.stop_timer.stop()
            self.movement_timer.stop()
            self.direction = random.choice([-1, 1])  # 随机选择一个方向
            self.set_new_timers()

        def stop_movement(self):
            self.stop_timer.stop()
            self.movement_timer.stop()
            self.direction = 0  # 停止移动
            self.set_new_timers()  # 重新设置停止时间和移动时间

        def update_position(self):
            if self.direction == 0:  # 如果宠物停止了移动
                return  # 不执行任何移动操作
            if self.direction != 0:
                current_pos = self.pos()
                if self.direction == 1:  # 向右移动
                    new_pos = QPoint(current_pos.x() + 1, current_pos.y())
                    if new_pos.x() >= self.max_x:
                        self.direction = -1  # 碰到右边界，掉头向左
                else:  # 向左移动
                    new_pos = QPoint(current_pos.x() - 1, current_pos.y())
                    if new_pos.x() <= 0:
                        self.direction = 1  # 碰到左边界，掉头向右
                self.move(new_pos)
            else:  # 停止移动
                self.stop_timer.stop()
                self.movement_timer.stop()
                stop_time = random.randint(2000, 5000)  # 生成一个2~5秒的随机数，作为移动时间
                self.stop_timer.start(stop_time)
            
        def random_speak(self):
            #待优化部分，应该是先区访问gpt，然后返回应该主动挑起的话题
            dialogues = ["我好无聊啊", "你想听个笑话吗？", "你有什么好玩的事情吗？", "你觉得我可爱吗？"]
            selected_dialogue = random.choice(dialogues)
            self.show_bubble(selected_dialogue)

        def show_bubble(self, text):
            if not text:
                return
            self.bubble.setText(text)
            self.bubble.adjustSize()
            global_position = self.mapToGlobal(QPoint(self.pet_label.width(), 0))
            self.bubble.move(global_position.x(), global_position.y() - self.bubble.height())
            # 将气泡框置于最底层
            self.bubble.lower()
            self.bubble.show()
            QTimer.singleShot(3000, self.bubble.hide)
    
        #设置界面
        def show_settings_dialog(self):
            settings_dialog = QDialog(self)
            settings_dialog.setWindowTitle("设置")
            settings_dialog.setFixedSize(400, 200)

            screen_geometry = QApplication.desktop().availableGeometry()
            screen_center = screen_geometry.center()
            settings_dialog.move(screen_center.x() - settings_dialog.width() // 2, screen_center.y() - settings_dialog.height() // 2)

            layout = QVBoxLayout()

            self.walk_checkbox = QCheckBox("是否自由走动", self)
            self.walk_checkbox.setChecked(self.timer.isActive())
            self.walk_checkbox.stateChanged.connect(self.toggle_walk)
            layout.addWidget(self.walk_checkbox)

            self.random_question_checkbox = QCheckBox("是否随机提问", self)
            self.random_question_checkbox.setChecked(self.stop_timer.isActive())
            self.random_question_checkbox.stateChanged.connect(self.toggle_random_question)
            layout.addWidget(self.random_question_checkbox)

            change_size_button = QPushButton("调整大小", self)
            change_size_button.clicked.connect(self.change_size)
            layout.addWidget(change_size_button)

            openai_key_layout = QHBoxLayout()
            openai_key_label = QLabel("OpenAI Key:")
            self.openai_key_input = QLineEdit()
            self.openai_key_input.setText(self.config.get("OpenAI", "openai_api_key"))
            openai_key_layout.addWidget(openai_key_label)
            openai_key_layout.addWidget(self.openai_key_input)
            layout.addLayout(openai_key_layout)

            chat_window_shortcut_layout = QHBoxLayout()
            chat_window_shortcut_label = QLabel("本地聊天框快捷键:")
            self.chat_window_shortcut_input = QKeySequenceEdit()
            self.chat_window_shortcut_input.setKeySequence(QKeySequence(self.config.get("Pet", "Shortcuts_CHAT_WINDOW")))
            chat_window_shortcut_layout.addWidget(chat_window_shortcut_label)
            chat_window_shortcut_layout.addWidget(self.chat_window_shortcut_input)
            layout.addLayout(chat_window_shortcut_layout)

            chat_web_shortcut_layout = QHBoxLayout()
            chat_web_shortcut_label = QLabel("学术优化快捷键:")
            self.chat_web_shortcut_input = QKeySequenceEdit()
            self.chat_web_shortcut_input.setKeySequence(QKeySequence(self.config.get("Pet", "Shortcuts_CHAT_WEB")))
            chat_web_shortcut_layout.addWidget(chat_web_shortcut_label)
            chat_web_shortcut_layout.addWidget(self.chat_web_shortcut_input)
            layout.addLayout(chat_web_shortcut_layout)

            ok_button = QPushButton("确定", self)
            ok_button.clicked.connect(lambda: self.save_all_config(self.walk_checkbox.isChecked(), self.random_question_checkbox.isChecked(), self.openai_key_input.text(), self.chat_window_shortcut_input.keySequence().toString(), self.chat_web_shortcut_input.keySequence().toString()))
            ok_button.clicked.connect(settings_dialog.accept)
            layout.addWidget(ok_button)

            settings_dialog.setLayout(layout)
            settings_dialog.exec_()

        def save_all_config(self, random_walk, random_chat, openai_key, chat_window_shortcut,chat_web_shortcut):
            self.config.set('Pet', 'RANDOM_WALK', str(random_walk))
            self.config.set('Pet', 'RANDOM_CHAT', str(random_chat))
            self.config.set("OpenAI", "openai_api_key", openai_key)
            self.config.set("Pet", "Shortcuts_CHAT_WINDOW", chat_window_shortcut)
            self.config.set("Pet", "Shortcuts_CHAT_WEB", chat_web_shortcut)
            self.save_config()

        def run_chat_web(self):
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                auto_opentab_delay()
                self.url = f"http://0.0.0.0:{PORT}?__dark-theme=true"
                demo.queue(concurrency_count=CONCURRENT_COUNT).launch(
                    server_name="0.0.0.0",
                    server_port=PORT,
                    auth=AUTHENTICATION,
                )
            finally:
                loop.close()

        def open_webpage(self):
            import webbrowser
            # Add your code to open the webpage here. This depends on the browser and how you want to open the webpage.
            webbrowser.open(self.url, new=0, autoraise=True)

        def toggle_chat_web(self):
            if self.chat_web_thread is None:
                self.chat_web_thread = threading.Thread(target=self.run_chat_web)
                self.chat_web_thread.start()
            else:
                self.open_webpage()
            

        #快捷键打开网页版窗口
        # def toggle_chat_web(self):
        #     def run_chat_web():
        #         import asyncio
        #         loop = asyncio.new_event_loop()
        #         asyncio.set_event_loop(loop)
        #         try:
        #             auto_opentab_delay()
        #             demo.queue(concurrency_count=CONCURRENT_COUNT).launch(server_name="0.0.0.0", server_port=PORT, auth=AUTHENTICATION)
        #         finally:
        #             loop.close()

        #     chat_web_thread = threading.Thread(target=run_chat_web)
        #     chat_web_thread.start()

        #由于keyboard库的add_hotkey函数在主线程中运行，从而阻塞了Qt事件循环导致的。为了解决这个问题，我们可以在一个单独的线程中运行全局快捷键监听器。
        def _run_keyboard_listener(self):
            chat_window_shortcut = self.config.get("Pet", "Shortcuts_CHAT_WINDOW")
            chat_web_shortcut = self.config.get("Pet", "Shortcuts_CHAT_WEB")
            keyboard.add_hotkey(chat_window_shortcut, lambda: QTimer.singleShot(0, pet.toggle_chat_window))
            keyboard.add_hotkey(chat_web_shortcut, lambda: QTimer.singleShot(0, pet.toggle_chat_web))
            keyboard.wait()
            

        def set_chat_window_closed(self):
            self.chat_window_open = False

        # 控制宠物自由走动和随机提问功能
        def toggle_walk(self, state):
            if state:
                self.timer.start(50)
            else:
                self.timer.stop()
        
        def change_size(self):
            flags = Qt.WindowSystemMenuHint | Qt.WindowTitleHint

            # 宽度输入框
            width_input_dialog = QInputDialog(self, flags)
            width_input_dialog.setWindowTitle("调整宽度")
            width_input_dialog.setLabelText("请输入新的宽度：")
            width_input_dialog.setIntRange(10, 500)
            width_input_dialog.setIntValue(self.pet_width)
            width_input_dialog.finished.connect(lambda: width_input_dialog.deleteLater())

            screen_geometry = QApplication.desktop().availableGeometry()
            screen_center = screen_geometry.center()
            width_input_dialog.move(screen_center.x() - width_input_dialog.width() // 2, screen_center.y() - width_input_dialog.height() // 2)

            result = width_input_dialog.exec_()
            if result == QInputDialog.Accepted:
                new_width = width_input_dialog.intValue()
                self.pet_width = new_width
                self.config.set("Pet", "WIDTH", str(new_width))

            # 高度输入框
            height_input_dialog = QInputDialog(self, flags)
            height_input_dialog.setWindowTitle("调整高度")
            height_input_dialog.setLabelText("请输入新的高度：")
            height_input_dialog.setIntRange(10, 500)
            height_input_dialog.setIntValue(self.pet_height)
            height_input_dialog.finished.connect(lambda: height_input_dialog.deleteLater())

            height_input_dialog.move(screen_center.x() - height_input_dialog.width() // 2, screen_center.y() - height_input_dialog.height() // 2)

            result = height_input_dialog.exec_()
            if result == QInputDialog.Accepted:
                new_height = height_input_dialog.intValue()
                self.pet_height = new_height
                self.config.set("Pet", "HEIGHT", str(new_height))

            self.pet_movie.setScaledSize(QSize(self.pet_width, self.pet_height))

            # 保存修改后的配置文件
            self.save_config()

        def toggle_random_question(self, state):
            if state == Qt.Checked and not self.isHidden():
                self.stop_timer.start()
            else:
                self.stop_timer.stop()
        
        def show_pet(self):
            # self.show()
            if self.stop_timer.isActive():
                self.bubble.show()

        def hide_pet(self):
            # self.hide()
            self.bubble.hide()

        def save_config(self):
            with codecs.open(config_private, 'w', 'utf-8') as f:
                self.config.write(f) 

    config_private = 'pet_config_private.ini'
    app = QApplication(sys.argv)
    config = configparser.ConfigParser()
    with codecs.open(config_private, 'r', 'utf-8') as f:
        # 读取配置文件内容
        config = configparser.ConfigParser()
        config.read_file(f)
    pet = DesktopPet(config)
    sys.exit(app.exec_())

    # 移动到宠物的聊天监听中，可以快捷键打开。具体查看toggle_chat_web
    #auto_opentab_delay()
    #demo.queue(concurrency_count=CONCURRENT_COUNT).launch(server_name="0.0.0.0", server_port=PORT, auth=AUTHENTICATION, favicon_path="docs/logo.png")

if __name__ == "__main__":
    main()