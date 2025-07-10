import os
from typing import List, Tuple, Optional
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QListWidget, QListWidgetItem, QFileDialog,
                            QCheckBox, QSlider, QLabel, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QKeyEvent
from .draw_on_pic import DrawOnPic
from .index_list import IndexQListWidgetItem

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.choose_one = False
        self.focus_index = -1
        self.classes: List[Tuple[int, str]] = []
        
        self.init_ui()
        self.connect_signals()
        
        # 设置焦点以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Helios Label Tool - Python")
        self.setGeometry(100, 100, 1600, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧控制面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel)
        
        # 中央图像显示区域
        self.image_label = DrawOnPic()
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        main_layout.addWidget(self.image_label, 1)
        
        # 右侧信息面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        
        # 文件夹选择按钮
        self.dir_button = QPushButton("选择图片文件夹")
        layout.addWidget(self.dir_button)
        
        # 标签文件选择按钮
        self.label_button = QPushButton("选择标签文件")
        layout.addWidget(self.label_button)
        
        # 模型文件选择按钮
        self.model_button = QPushButton("选择模型文件")
        layout.addWidget(self.model_button)
        
        # 文件列表滑块和标签
        slider_layout = QHBoxLayout()
        self.file_slider = QSlider(Qt.Horizontal)
        self.file_label = QLabel("[0/0]")
        slider_layout.addWidget(self.file_slider)
        slider_layout.addWidget(self.file_label)
        layout.addLayout(slider_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(200)
        layout.addWidget(self.file_list)
        
        # 工作模式列表
        mode_label = QLabel("工作模式:")
        layout.addWidget(mode_label)
        self.mode_list = QListWidget()
        self.mode_list.addItem("norm")
        self.mode_list.addItem("armor") 
        self.mode_list.addItem("energy")
        self.mode_list.setMaximumHeight(100)
        layout.addWidget(self.mode_list)
        
        # 智能检测按钮
        self.smart_button = QPushButton("智能检测")
        layout.addWidget(self.smart_button)
        
        # 全部智能检测按钮
        self.smart_all_button = QPushButton("全部智能检测")
        layout.addWidget(self.smart_all_button)
        
        # 添加标签按钮
        self.add_label_button = QPushButton("添加标签")
        layout.addWidget(self.add_label_button)
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        layout.addWidget(self.save_button)
        
        # 自动保存复选框
        self.auto_save_checkbox = QCheckBox("自动保存")
        layout.addWidget(self.auto_save_checkbox)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        
        # 类别列表
        class_label = QLabel("类别列表:")
        layout.addWidget(class_label)
        self.class_list = QListWidget()
        self.class_list.setMaximumHeight(200)
        layout.addWidget(self.class_list)
        
        # 当前标签列表
        current_label = QLabel("当前标签:")
        layout.addWidget(current_label)
        self.label_now_list = QListWidget()
        self.label_now_list.setMaximumHeight(200)
        layout.addWidget(self.label_now_list)
        
        layout.addStretch()
        return panel
    
    def connect_signals(self):
        """连接信号和槽"""
        # 按钮信号
        self.dir_button.clicked.connect(self.on_dir_button_clicked)
        self.label_button.clicked.connect(self.on_label_button_clicked)
        self.model_button.clicked.connect(self.on_model_button_clicked)
        self.add_label_button.clicked.connect(self.image_label.set_add_mode)
        self.save_button.clicked.connect(self.image_label.save_as_txt)
        self.smart_button.clicked.connect(self.image_label.smart_detect)
        self.smart_all_button.clicked.connect(self.on_smart_all_clicked)
        
        # 复选框信号
        self.auto_save_checkbox.clicked.connect(self.image_label.auto_save_toggle)
        
        # 列表信号
        self.file_list.currentItemChanged.connect(self.on_file_list_changed)
        self.class_list.itemClicked.connect(self.on_class_list_clicked)
        self.label_now_list.itemClicked.connect(self.on_label_now_clicked)
        self.mode_list.itemClicked.connect(self.on_mode_list_clicked)
        
        # 滑块信号
        self.file_slider.valueChanged.connect(self.on_slider_changed)
        self.file_slider.rangeChanged.connect(self.on_slider_range_changed)
        
        # 图像标签信号
        self.image_label.doubleClicked.connect(self.refresh_label_list)
    
    @pyqtSlot()
    def on_dir_button_clicked(self):
        """选择图片文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if not folder:
            return
        
        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        # 清空列表
        self.file_list.clear()
        
        # 获取图片文件
        image_files = []
        for file_name in os.listdir(folder):
            if any(file_name.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(folder, file_name))
        
        # 排序并添加到列表
        image_files.sort()
        for idx, file_path in enumerate(image_files):
            item = IndexQListWidgetItem(file_path, idx)
            self.file_list.addItem(item)
        
        # 设置滑块范围
        if image_files:
            self.file_slider.setMinimum(1)
            self.file_slider.setMaximum(len(image_files))
            self.file_slider.setValue(1)
            self.file_list.setCurrentRow(0)
    
    @pyqtSlot()
    def on_label_button_clicked(self):
        """选择标签文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择标签文件", "", "文本文件 (*.txt)")
        
        if file_path:
            folder_path = os.path.dirname(file_path)
            self.image_label.set_label_path(file_path, folder_path)
            
            # 更新类别列表
            self.classes = self.image_label.get_all_classes()
            self.class_list.clear()
            for cls_id, cls_name in self.classes:
                self.class_list.addItem(QListWidgetItem(cls_name))
            
            if self.class_list.count() > 0:
                self.class_list.setCurrentRow(0)
    
    @pyqtSlot()
    def on_model_button_clicked(self):
        """选择模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", "", "ONNX模型 (*.onnx)")
        
        if file_path:
            self.image_label.set_model_file(file_path)
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_file_list_changed(self, current, previous):
        """文件列表改变"""
        if current is None:
            return
        
        self.image_label.set_current_file(current.text())
        self.refresh_label_list()
        
        # 更新滑块
        if isinstance(current, IndexQListWidgetItem):
            self.file_slider.setValue(current.get_index() + 1)
    
    @pyqtSlot(QListWidgetItem)
    def on_class_list_clicked(self, item):
        """类别列表点击"""
        if item is None:
            return
        
        if not self.choose_one:
            self.image_label.set_class(item.text())
        else:
            self.image_label.set_focus_class(self.focus_index, item.text())
            self.choose_one = False
        
        self.refresh_label_list()
    
    @pyqtSlot(QListWidgetItem)
    def on_label_now_clicked(self, item):
        """当前标签列表点击"""
        if item is None:
            return
        
        self.focus_index = self.label_now_list.row(item)
        self.choose_one = True
        self.image_label.draw_focus(self.focus_index)
    
    @pyqtSlot(QListWidgetItem)
    def on_mode_list_clicked(self, item):
        """模式列表点击"""
        if item is None:
            return
        
        mode_text = item.text()
        if mode_text == "armor":
            self.image_label.set_work_mode(0)  # ARMOR
        elif mode_text == "energy":
            self.image_label.set_work_mode(1)  # ENERGY
        elif mode_text == "norm":
            self.image_label.set_work_mode(2)  # NORM
    
    @pyqtSlot(int)
    def on_slider_changed(self, value):
        """滑块值改变"""
        self.file_label.setText(f"[{value}/{self.file_slider.maximum()}]")
        if 1 <= value <= self.file_list.count():
            self.file_list.setCurrentRow(value - 1)
    
    @pyqtSlot(int, int)
    def on_slider_range_changed(self, min_val, max_val):
        """滑块范围改变"""
        current = self.file_slider.value()
        self.file_label.setText(f"[{current}/{max_val}]")
    
    @pyqtSlot()
    def on_smart_all_clicked(self):
        """全部智能检测"""
        total = self.file_list.count()
        if total == 0:
            return
        
        for i in range(total):
            self.file_list.setCurrentRow(i)
            self.image_label.smart_detect()
            QApplication.processEvents()  # 更新UI
    
    def refresh_label_list(self):
        """刷新标签列表"""
        labels = self.image_label.get_labels_now()
        self.label_now_list.clear()
        
        for label in labels:
            # 查找类别名称
            class_name = "unknown"
            for cls_id, cls_name in self.classes:
                if cls_id == label.get_class():
                    class_name = cls_name
                    break
            self.label_now_list.addItem(QListWidgetItem(class_name))
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        key = event.key()
        current_row = self.file_list.currentRow()
        
        if key == Qt.Key_Q:  # 上一张图片
            if current_row > 0:
                self.file_list.setCurrentRow(current_row - 1)
        elif key == Qt.Key_E:  # 下一张图片
            if current_row < self.file_list.count() - 1:
                self.file_list.setCurrentRow(current_row + 1)
        elif key == Qt.Key_S:  # 智能检测
            self.image_label.smart_detect()
        elif key == Qt.Key_Space:  # 添加标签
            self.image_label.set_add_mode()
        else:
            super().keyPressEvent(event)