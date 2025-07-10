import os
from typing import Optional, List, Tuple
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QImage, QPainter, QTransform, QWheelEvent, QMouseEvent
from .qt_painter import Painter
from .txt_manager import AllLabel
from .label_manager import OneLabel
from .model import SmartAdd

# 模式常量
MOVE = 0
ADD = 1

# 工作模式常量
ARMOR = 0
ENERGY = 1
NORM = 2

class DrawOnPic(QLabel):
    """图像绘制和标注组件"""
    
    doubleClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化变量
        self.mode = MOVE
        self.work_mode = NORM
        self.auto_save = False
        self.have_focus = False
        self.focus_label = -1
        
        # 图像相关
        self.current_file = ""
        self.image_name = ""
        self.img: Optional[QImage] = None
        self.img2label = QTransform()
        
        # 鼠标操作相关
        self.last_pos = QPointF(0, 0)
        self.drag_offset = QPointF(0, 0)
        self.drag_point: Optional[QPointF] = None
        
        # 组件
        self.painter = Painter()
        self.all_label = AllLabel(4)
        self.model = SmartAdd()
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
    
    def set_current_file(self, file_path: str):
        """设置当前文件"""
        if self.auto_save:
            self.save_as_txt()
        
        self.img2label.reset()
        self.current_file = file_path
        self.image_name = self.get_pic_name(file_path)
        self.load_image()
        self.all_label.set_image_name(self.image_name)
        self.draw()
    
    def get_pic_name(self, file_path: str) -> str:
        """从文件路径获取文件名（不含扩展名）"""
        return os.path.splitext(os.path.basename(file_path))[0]
    
    def load_image(self):
        """加载图像"""
        if self.painter.painter_label:
            self.painter.painter_label.end()
        
        self.img = QImage()
        self.all_label.reset()
        
        if not self.img.load(self.current_file):
            print(f"Failed to load image: {self.current_file}")
            return
        
        self.painter.reset_painter(self.img)
        self.all_label.set_pic_size(self.img.height(), self.img.width())
        
        # 计算缩放比例以适应标签大小
        label_size = self.size()
        img_size = self.img.size()
        
        scale_x = label_size.width() / img_size.width()
        scale_y = label_size.height() / img_size.height()
        scale = min(scale_x, scale_y)
        
        transform = QTransform()
        transform.scale(scale, scale)
        self.img2label = transform
    
    def paintEvent(self, event):
        """绘制事件"""
        if not self.img:
            return
        
        painter = QPainter(self)
        painter.setTransform(self.img2label)
        painter.drawImage(0, 0, self.img)
    
    def wheelEvent(self, event: QWheelEvent):
        """滚轮事件 - 缩放"""
        delta = 1.1 if event.angleDelta().y() > 0 else 1/1.1
        
        transform = QTransform()
        transform.scale(delta, delta)
        self.img2label = self.img2label * transform
        self.draw()
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.RightButton:
            self.last_pos = event.pos()
        elif event.button() == Qt.LeftButton:
            true_point = self.img2label.inverted()[0].map(QPointF(event.pos()))
            
            if self.mode == MOVE:
                self.drag_point = self.find_move_point(true_point)
                if self.drag_point:
                    self.drag_offset = true_point - self.drag_point
        
        self.draw()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if event.buttons() & Qt.RightButton:
            # 拖拽图像
            delta = QPointF(event.pos()) - self.last_pos
            self.last_pos = QPointF(event.pos())
            
            transform = QTransform()
            transform.translate(delta.x(), delta.y())
            self.img2label = self.img2label * transform
            self.draw()
        
        elif event.buttons() & Qt.LeftButton and self.mode == MOVE:
            # 拖拽点
            if self.drag_point:
                true_point = self.img2label.inverted()[0].map(QPointF(event.pos()))
                new_pos = true_point - self.drag_offset
                self.drag_point.setX(new_pos.x())
                self.drag_point.setY(new_pos.y())
                self.draw()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.mode == ADD:
            self.add_point(event)
        
        self.drag_offset = QPointF(0, 0)
        self.drag_point = None
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击事件 - 删除"""
        if event.button() == Qt.RightButton:
            if self.have_focus:
                self.all_label.erase_focus(self.focus_label)
                self.have_focus = False
            else:
                self.all_label.erase_last()
            self.draw()
            self.doubleClicked.emit()
    
    def add_point(self, event: QMouseEvent):
        """添加点"""
        if self.all_label.label_now.size() == self.all_label.get_num():
            self.all_label.label_now.reset()
        
        true_point = self.img2label.inverted()[0].map(QPointF(event.pos()))
        self.all_label.set_point(true_point)
        
        if self.all_label.label_now.size() == self.all_label.label_now.get_num():
            self.set_move_mode()
        
        self.draw()
    
    def find_move_point(self, mouse_pos: QPointF) -> Optional[QPointF]:
        """查找可移动的点"""
        if not self.all_label.labels_in_pic:
            return None
        
        max_dist = 10
        closest_point = None
        
        for label in self.all_label.labels_in_pic:
            for point in label.label_points:
                dist = (point - mouse_pos).manhattanLength()
                if dist < max_dist:
                    max_dist = dist
                    closest_point = point
        
        return closest_point
    
    def draw(self):
        """绘制图像和标注"""
        if self.painter.painter_label:
            self.painter.painter_label.end()
        
        self.img = QImage()
        if not self.img.load(self.current_file):
            return
        
        self.painter.reset_painter(self.img)
        self.painter.draw(self.all_label)
        self.update()
    
    def set_apex_num(self, text: str):
        """设置顶点数量"""
        try:
            num = int(text)
            self.all_label = AllLabel(num)
            self.model.set_num_points(num)
        except ValueError:
            pass
    
    def set_add_mode(self):
        """设置添加模式"""
        if not self.img:
            return
        self.mode = ADD
        self.all_label.label_now.reset()
        self.draw()
    
    def set_move_mode(self):
        """设置移动模式"""
        if not self.img:
            return
        self.mode = MOVE
        self.draw()
    
    def set_class(self, cls_name: str):
        """设置类别"""
        if not self.all_label.set_class(cls_name):
            print("Error setting class")
        self.draw()
    
    def set_focus_class(self, index: int, cls_name: str):
        """设置焦点标签的类别"""
        self.all_label.set_focus_class(index, cls_name)
        self.draw()
    
    def draw_focus(self, index: int):
        """绘制焦点标签"""
        self.draw()
        if 0 <= index < len(self.all_label.labels_in_pic):
            self.focus_label = index
            self.have_focus = True
            focus_label = self.all_label.labels_in_pic[index]
            self.painter.draw_focus(focus_label)
            self.update()
    
    def set_label_path(self, file_path: str, folder_path: str):
        """设置标签路径"""
        self.all_label.set_label_path(file_path, folder_path)
        self.model.set_num_class(self.all_label.get_all_class_num())
    
    def get_all_classes(self) -> List[Tuple[int, str]]:
        """获取所有类别"""
        return self.all_label.get_all_classes()
    
    def get_labels_now(self) -> List[OneLabel]:
        """获取当前标签"""
        return self.all_label.labels_in_pic
    
    def save_as_txt(self):
        """保存为txt文件"""
        self.all_label.save_as_txt()
    
    def auto_save_toggle(self, checked: bool):
        """切换自动保存"""
        self.auto_save = checked
    
    def set_model_file(self, model_path: str):
        """设置模型文件"""
        if self.work_mode in [ARMOR, ENERGY]:
            self.model.set_model(model_path)
        else:
            print("Error: wrong mode for model")
    
    def set_work_mode(self, mode: int):
        """设置工作模式"""
        self.work_mode = mode
        
        if mode == ARMOR:
            self.model.set_num_class(16)
            self.model.set_num_points(4)
            self.all_label = AllLabel(4)
        elif mode == ENERGY:
            self.model.set_num_class(6)
            self.model.set_num_points(4)
            self.all_label = AllLabel(4)
    
    def smart_detect(self):
        """智能检测"""
        if self.work_mode in [ARMOR, ENERGY]:
            self.all_label.reset()
            success = self.model.detect(self.current_file, self.all_label.labels_in_pic)
            if success:
                self.doubleClicked.emit()
                self.save_as_txt()
        self.draw()