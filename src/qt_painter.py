from PyQt5.QtGui import QPainter, QPen, QFont, QImage
from PyQt5.QtCore import Qt, QPointF
from typing import Optional
from .txt_manager import AllLabel
from .label_manager import OneLabel

class Painter:
    """绘制器类"""
    
    def __init__(self):
        self.painter_label: Optional[QPainter] = None
        self.pen_point = QPen(Qt.green, 3)
        self.pen_line = QPen(Qt.red, 2)
        self.pen_focus = QPen(Qt.blue, 3)
        self.font = QFont("Arial", 12)
    
    def reset_painter(self, img: QImage):
        """重置画笔"""
        if self.painter_label:
            self.painter_label.end()
        self.painter_label = QPainter(img)
    
    def draw_point(self, point: QPointF):
        """绘制点"""
        if self.painter_label:
            self.painter_label.setPen(self.pen_point)
            self.painter_label.drawEllipse(point, 3, 3)
    
    def draw_line(self, points: list, num_points: int):
        """绘制连线"""
        if self.painter_label and len(points) >= 2:
            self.painter_label.setPen(self.pen_line)
            for i in range(num_points):
                if i < len(points) and (i + 1) % num_points < len(points):
                    self.painter_label.drawLine(points[i], points[(i + 1) % num_points])
    
    def draw_text(self, point: QPointF, text: str):
        """绘制文本"""
        if self.painter_label:
            self.painter_label.setFont(self.font)
            self.painter_label.setPen(Qt.green)
            self.painter_label.drawText(point, text)
    
    def draw(self, all_label: AllLabel) -> bool:
        """绘制所有标签"""
        if not self.painter_label:
            return False
        
        success = False
        
        # 绘制已完成的标签
        for label in all_label.labels_in_pic:
            text = all_label.get_class_string(label)
            if label.label_points:
                self.draw_text(label.label_points[0], text)
                self.draw_line(label.label_points, label.get_num())
                for point in label.label_points:
                    self.draw_point(point)
            success = True
        
        # 绘制当前标签
        if not all_label.label_now.empty():
            for point in all_label.label_now.label_points:
                self.draw_point(point)
            success = True
        
        return success
    
    def draw_focus(self, label: OneLabel) -> bool:
        """绘制焦点标签"""
        if not self.painter_label:
            return False
        
        self.painter_label.setPen(self.pen_focus)
        num_points = label.size()
        
        for i in range(num_points):
            if i < len(label.label_points):
                # 绘制连线
                next_i = (i + 1) % num_points
                if next_i < len(label.label_points):
                    self.painter_label.drawLine(label.label_points[i], label.label_points[next_i])
                # 绘制点编号
                self.painter_label.drawText(label.label_points[i], str(i))
        
        return True