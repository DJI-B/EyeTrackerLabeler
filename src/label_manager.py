from typing import List, Optional
from PyQt5.QtCore import QPointF

class OneLabel:
    """单个标签管理类"""
    
    def __init__(self, num_points: int = 0):
        self.num_points = num_points
        self.label_points: List[QPointF] = []
        self.label_class = 0
        self.has_class = False
        self.has_points = False
    
    def set_point(self, point: QPointF) -> bool:
        """设置点"""
        if len(self.label_points) >= self.num_points:
            return False
        self.label_points.append(point)
        if len(self.label_points) == self.num_points:
            self.has_points = True
        return True
    
    def set_point_flexible(self, point: QPointF):
        """灵活设置点（可变数量）"""
        self.label_points.append(point)
        self.num_points = len(self.label_points)
        self.has_points = True
    
    def set_class(self, cls: int) -> bool:
        """设置类别"""
        if not self.has_points:
            return False
        self.label_class = cls
        self.has_class = True
        return True
    
    def get_class(self) -> int:
        return self.label_class
    
    def get_num(self) -> int:
        return self.num_points
    
    def size(self) -> int:
        return len(self.label_points)
    
    def success(self) -> bool:
        return self.has_class and self.has_points
    
    def reset(self):
        """重置标签"""
        self.label_points.clear()
        self.has_class = False
        self.has_points = False
    
    def empty(self) -> bool:
        return len(self.label_points) == 0
    
    def erase_last(self) -> bool:
        """删除最后一个点"""
        if not self.label_points:
            return False
        self.label_points.pop()
        if len(self.label_points) < self.num_points:
            self.has_points = False
        return True
    
    def __getitem__(self, index: int) -> QPointF:
        return self.label_points[index]
    
    def __setitem__(self, index: int, value: QPointF):
        self.label_points[index] = value