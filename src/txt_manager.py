import os
from typing import List, Tuple, Optional
from PyQt5.QtCore import QPointF
from .label_manager import OneLabel

class AllLabel:
    """所有标签管理类"""
    
    def __init__(self, num_points: int = 4):
        self.num_points = num_points
        self.label_now = OneLabel(num_points)
        self.labels_in_pic: List[OneLabel] = []
        self.label_classes: List[Tuple[int, str]] = []
        self.image_width = 0
        self.image_height = 0
        self.file_path = ""
        self.folder_path = ""
        self.image_name = ""
    
    def set_point(self, point: QPointF) -> bool:
        """设置点"""
        return self.label_now.set_point(point)
    
    def set_class(self, cls_name: str) -> bool:
        """设置类别"""
        for cls_id, name in self.label_classes:
            if name == cls_name:
                if self.label_now.set_class(cls_id) and self.label_now.success():
                    self.labels_in_pic.append(self.label_now)
                    self.label_now = OneLabel(self.num_points)
                    return True
        return False
    
    def set_focus_class(self, index: int, cls_name: str) -> bool:
        """设置焦点标签的类别"""
        if 0 <= index < len(self.labels_in_pic):
            for cls_id, name in self.label_classes:
                if name == cls_name:
                    return self.labels_in_pic[index].set_class(cls_id)
        return False
    
    def get_class_string(self, label: OneLabel) -> str:
        """获取类别字符串"""
        for cls_id, name in self.label_classes:
            if cls_id == label.get_class():
                return name
        return ""
    
    def get_num(self) -> int:
        return self.num_points
    
    def get_all_class_num(self) -> int:
        return len(self.label_classes)
    
    def reset(self):
        """重置所有标签"""
        self.labels_in_pic.clear()
        self.label_now.reset()
    
    def set_num(self, num: int):
        """设置点数"""
        self.num_points = num
        self.label_now = OneLabel(num)
    
    def set_pic_size(self, height: int, width: int):
        """设置图片尺寸"""
        self.image_height = height
        self.image_width = width
    
    def set_label_path(self, file_path: str, folder_path: str) -> bool:
        """设置标签路径"""
        self.file_path = file_path
        self.folder_path = os.path.join(folder_path, "labels")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.label_classes.clear()
                for line_num, line in enumerate(f):
                    cls_name = line.strip()
                    if cls_name:
                        self.label_classes.append((line_num, cls_name))
            return True
        except Exception as e:
            print(f"Error reading label file: {e}")
            return False
    
    def get_all_classes(self) -> List[Tuple[int, str]]:
        return self.label_classes
    
    def empty(self) -> bool:
        return len(self.labels_in_pic) == 0
    
    def erase_last(self):
        """删除最后一个元素"""
        if self.label_now.erase_last():
            return
        elif self.labels_in_pic:
            self.labels_in_pic.pop()
    
    def erase_focus(self, index: int):
        """删除指定索引的标签"""
        if 0 <= index < len(self.labels_in_pic):
            self.labels_in_pic.pop(index)
    
    def set_image_name(self, name: str):
        """设置图片名称并读取对应的txt文件"""
        self.image_name = name
        if self.folder_path:
            txt_path = os.path.join(self.folder_path, f"{name}.txt")
            if os.path.exists(txt_path):
                self.read_data_from_txt(txt_path)
    
    def read_data_from_txt(self, path: str):
        """从txt文件读取标注数据"""
        try:
            with open(path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 3:  # 至少需要类别和一个点的坐标
                        continue
                    
                    cls_id = int(parts[0])
                    label = OneLabel(0)  # 灵活点数
                    
                    # 读取点坐标
                    coords = parts[1:]
                    for i in range(0, len(coords), 2):
                        if i + 1 < len(coords):
                            x = float(coords[i]) * self.image_width
                            y = float(coords[i + 1]) * self.image_height
                            label.set_point_flexible(QPointF(x, y))
                    
                    label.set_class(cls_id)
                    self.labels_in_pic.append(label)
        except Exception as e:
            print(f"Error reading txt file {path}: {e}")
    
    def save_as_txt(self):
        """保存为txt文件"""
        if not self.folder_path or not self.image_name:
            print("Error: path not set")
            return
        
        # 确保labels文件夹存在
        os.makedirs(self.folder_path, exist_ok=True)
        
        file_path = os.path.join(self.folder_path, f"{self.image_name}.txt")
        
        try:
            if not self.empty():
                with open(file_path, 'w') as f:
                    for label in self.labels_in_pic:
                        f.write(f"{label.get_class()}")
                        for point in label.label_points:
                            x_norm = point.x() / self.image_width
                            y_norm = point.y() / self.image_height
                            f.write(f" {x_norm:.6f} {y_norm:.6f}")
                        f.write("\n")
            else:
                # 如果没有标签，删除文件（如果存在）
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Error saving txt file: {e}")