from PyQt5.QtWidgets import QDialog, QVBoxLayout, QSizePolicy,\
    QHBoxLayout, QLabel,QWidget, QScrollArea, QGridLayout, QSpacerItem
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFontMetrics

#聊天框的主体部分，展示相关
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

#每条消息的符复合组件
class MessageWidget(QWidget):
    def __init__(self, role, text, parent=None):
        super().__init__(parent)
        self.role = role
        self.text = text
        # 图像
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        avatar = QPixmap("pet_image\\avatar_{}.png".format(role)).scaledToWidth(30).scaledToHeight(30)
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