import sys
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QLabel, QGraphicsDropShadowEffect, QFileDialog, QDialog, QVBoxLayout, \
    QTextEdit, QPushButton, QLineEdit, QHBoxLayout, QInputDialog, QDesktopWidget, QCheckBox

from chat_model.chatdialog import  ChatWindow

import configparser
import random

#桌面宠物的类
class DesktopPet(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

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

    #初始化界面
    def init_ui(self):
        #父容器
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(256,256)
        screen_geometry = QApplication.desktop().availableGeometry()
        self.move(screen_geometry.width() - self.width()-500, screen_geometry.height() - self.height()-100)

        #宠物信息
        self.pet_icon = QIcon(self.config["Pet"]["PET_ICON"])
        self.pet_pixmap = self.pet_icon.pixmap(256,256)
        self.nickname = self.config["Pet"]["NICKNAME"]

        #右键功能区，可以自定义（擅长的朋友）
        self.menu = QMenu(self)
        #调用gpt聊天框
        chat_action = QAction("聊天", self, triggered=self.show_chat_dialog)

        change_icon_action = QAction("更换图标", self, triggered=self.change_icon)

        exit_action = QAction("退出", self, triggered=self.close)
        self.menu.addActions([chat_action, change_icon_action, exit_action])

        change_nickname_action = QAction("改昵称", self, triggered=self.change_nickname)
        self.menu.addActions([chat_action, change_icon_action, change_nickname_action, exit_action])

        settings_action = QAction("设置", self, triggered=self.show_settings_dialog)
        self.menu.addActions([chat_action, change_icon_action, change_nickname_action, settings_action, exit_action])

        #随机发起对话功能的气泡框
        self.bubble = QLabel(self.parent())
        self.bubble.setWindowFlags(Qt.SplashScreen)
        pet_width = self.pet_pixmap.width()
        pet_height = self.pet_pixmap.height()
        self.bubble.setGeometry(pet_width, -60, 200, 50)
        self.bubble.setStyleSheet("background-color: white; border-radius: 10px; padding: 5px;")
        self.bubble.hide()

        shadow_effect = QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2)
        self.bubble.setGraphicsEffect(shadow_effect)
        

    
        #聊天框，首先设置成隐藏，右键点击之后再显示
        # self.bubble = QLabel(self.parent())
        # pet_width = self.pet_pixmap.width()
        # pet_height = self.pet_pixmap.height()
        # self.bubble.setGeometry(pet_width, -60, 200, 50)
        # self.bubble.setStyleSheet("background-color: white; border-radius: 10px; padding: 5px;")
        # self.bubble.hide()

        # shadow_effect = QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2)
        # self.bubble.setGraphicsEffect(shadow_effect)

        self.show()

    #修改昵称
    def change_nickname(self):
        new_nickname, ok = QInputDialog.getText(self, "改昵称", "请输入新的昵称：", QLineEdit.Normal, self.nickname)
        if ok and new_nickname != '':
            self.nickname = new_nickname
            # 修改配置项
            self.config.set('Pet', 'NICKNAME', new_nickname)
            # 保存修改后的配置文件
            with open('private_config.ini', 'w') as f:
                config.write(f)

    #创建新的窗口，即gpt聊天框
    def show_chat_dialog(self):
        chat_window = ChatWindow(self,self.config)
        chat_window.show()
    
    #根据鼠标更新对话框位置
    def update_chat_dialog_position(self):
        if hasattr(self, 'chat_dialog') and self.chat_dialog.isVisible():
            dialog_position = self.mapToGlobal(QPoint(self.pet_pixmap.width() // 2, -self.chat_dialog.height()))
            self.chat_dialog.move(dialog_position)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, self.pet_pixmap)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            self.update_chat_dialog_position()
    # def mouseMoveEvent(self, event):
    #     if event.buttons() == Qt.LeftButton:
    #         self.move(event.globalPos() - self.drag_position)
    #         event.accept()

    def contextMenuEvent(self, event):
        self.menu.exec_(event.globalPos())

    #修改图标路径
    def change_icon(self):
        # 请在此处添加选择图标的逻辑，可以使用 QFileDialog 获取文件路径
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        new_icon_path, _ = QFileDialog.getOpenFileName(self, "选择新图标", "", "Images (*.png *.xpm *.jpg *.bmp);;All Files (*)", options=options)
        if new_icon_path:
            self.pet_icon = QIcon(new_icon_path)
            self.pet_pixmap = self.pet_icon.pixmap(128, 128)
            self.update()
            # 修改配置项
            self.config.set('Pet', 'PET_ICON', new_icon_path)

            # 保存修改后的配置文件
            with open('private_config.ini', 'w') as f:
                config.write(f)
    
    # 宠物移动相关
    # def enterEvent(self, event):
    #     if self.config.getboolean("Pet", "RANDOM_WALK"):
    #         self.timer.stop()

    # def leaveEvent(self, event):
    #     if self.config.getboolean("Pet", "RANDOM_WALK"):
    #         self.timer.start()

    def set_new_timers(self):
        stop_time = random.randint(2000, 5000)  # 生成一个2~5秒的随机数，作为移动时间
        self.stop_timer.start(stop_time)

        movement_time = random.randint(2000, 5000)  # 生成一个2~5秒的随机数，作为移动时间
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
            self.update_bubble_position()  # 更新气泡框位置
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
        global_position = self.mapToGlobal(QPoint(self.pet_pixmap.width(), 0))
        self.bubble.move(global_position.x(), global_position.y() - self.bubble.height())
        self.bubble.show()
        QTimer.singleShot(3000, self.bubble.hide)

    #气泡框随着移动
    def update_bubble_position(self):
        if self.bubble.isVisible():
            global_position = self.mapToGlobal(QPoint(self.pet_pixmap.width(), 0))
            self.bubble.move(global_position.x(), global_position.y() - self.bubble.height())
    #设置界面
    def show_settings_dialog(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("设置")
        settings_dialog.setFixedSize(300, 150)

        layout = QVBoxLayout()

        walk_checkbox = QCheckBox("是否自由走动", self)
        walk_checkbox.setChecked(self.timer.isActive())
        walk_checkbox.stateChanged.connect(self.toggle_walk)
        layout.addWidget(walk_checkbox)
        self.config.set('Pet', 'RANDOM_WALK', str(walk_checkbox.isChecked()))
        # 保存修改后的配置文件
        with open('private_config.ini', 'w') as f:
            config.write(f)
        
        random_question_checkbox = QCheckBox("是否随机提问", self)
        random_question_checkbox.setChecked(self.stop_timer.isActive())
        random_question_checkbox.stateChanged.connect(self.toggle_random_question)
        layout.addWidget(random_question_checkbox)
        self.config.set('Pet', 'RANDOM_CHAT', str(random_question_checkbox.isChecked()))
        # 保存修改后的配置文件
        with open('private_config.ini', 'w') as f:
            config.write(f)

        ok_button = QPushButton("确定", self)
        ok_button.clicked.connect(settings_dialog.accept)
        layout.addWidget(ok_button)

        settings_dialog.setLayout(layout)
        settings_dialog.exec_()

    # 控制宠物自由走动和随机提问功能
    def toggle_walk(self, state):
        if state:
            self.timer.start(50)
        else:
            self.timer.stop()


    def toggle_random_question(self, state):
        if state == Qt.Checked and not self.isHidden():
            self.stop_timer.start()
        else:
            self.stop_timer.stop()
    
    def show_pet(self):
        self.show()
        if self.stop_timer.isActive():
            self.bubble.show()

    def hide_pet(self):
        self.hide()
        self.bubble.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = configparser.ConfigParser()
    with open('private_config.ini', encoding='utf-8') as f:
        config.read_file(f)
    pet = DesktopPet(config)
    sys.exit(app.exec_())

