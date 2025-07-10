import cv2
import numpy as np
from typing import List, Tuple, Optional
from PyQt5.QtCore import QPointF
from .label_manager import OneLabel

# 尝试导入OpenVINO，如果失败则使用模拟版本
try:
    import openvino as ov
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False
    print("Warning: OpenVINO not available. Smart detection will be disabled.")

class Object:
    """检测对象"""
    def __init__(self):
        self.label = 0
        self.color = 0
        self.conf = 0.0
        self.points: List[Tuple[float, float]] = []
        self.rect = (0, 0, 0, 0)  # x, y, w, h

class SmartAdd:
    """智能标注类"""
    
    def __init__(self):
        self.num_classes = 9
        self.num_points = 4
        self.model_path = ""
        self.input_width = 640
        self.input_height = 640
        self.conf_thresh = 0.6
        self.nms_thresh = 0.3
        
        # OpenVINO相关
        if OPENVINO_AVAILABLE:
            self.core = ov.Core()
            self.compiled_model = None
            self.infer_request = None
        else:
            self.core = None
    
    def set_num_class(self, num: int):
        """设置类别数量"""
        self.num_classes = num // 2  # 除以颜色数
    
    def set_num_points(self, points: int):
        """设置点数"""
        self.num_points = points
    
    def set_model(self, model_path: str) -> bool:
        """设置模型路径"""
        if not OPENVINO_AVAILABLE:
            print("OpenVINO not available")
            return False
        
        try:
            self.model_path = model_path
            model = self.core.read_model(self.model_path)
            self.compiled_model = self.core.compile_model(model, "CPU")
            self.infer_request = self.compiled_model.create_infer_request()
            
            # 获取输入形状
            input_layer = self.compiled_model.input(0)
            input_shape = input_layer.shape
            if len(input_shape) == 4:  # NCHW或NHWC
                self.input_height = input_shape[2]
                self.input_width = input_shape[3]
            
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """预处理图像"""
        # 调整大小
        resized = cv2.resize(img, (self.input_width, self.input_height))
        
        # 转换为浮点并归一化
        resized = resized.astype(np.float32) / 255.0
        
        # 转换为CHW格式
        resized = np.transpose(resized, (2, 0, 1))
        
        # 添加batch维度
        resized = np.expand_dims(resized, axis=0)
        
        return resized
    
    def postprocess(self, output: np.ndarray, original_shape: Tuple[int, int]) -> List[Object]:
        """后处理输出"""
        objects = []
        
        # 这里需要根据具体的模型输出格式来实现
        # 以下是示例实现，需要根据实际模型调整
        
        if output.ndim == 3:
            output = output[0]  # 移除batch维度
        
        # 假设输出格式为 [num_detections, class + conf + points]
        for detection in output:
            if len(detection) < self.num_points * 2 + 2:  # 至少需要置信度 + 类别 + 点坐标
                continue
            
            conf = detection[0]
            if conf < self.conf_thresh:
                continue
            
            obj = Object()
            obj.conf = conf
            obj.label = int(detection[1]) if len(detection) > 1 else 0
            
            # 提取点坐标
            scale_x = original_shape[1] / self.input_width
            scale_y = original_shape[0] / self.input_height
            
            for i in range(self.num_points):
                if 2 + i * 2 + 1 < len(detection):
                    x = detection[2 + i * 2] * scale_x
                    y = detection[2 + i * 2 + 1] * scale_y
                    obj.points.append((x, y))
            
            if len(obj.points) == self.num_points:
                objects.append(obj)
        
        return objects
    
    def detect(self, img_path: str, target: List[OneLabel]) -> bool:
        """检测函数"""
        if not OPENVINO_AVAILABLE or not self.compiled_model:
            print("Model not loaded or OpenVINO not available")
            return False
        
        try:
            # 读取图像
            img = cv2.imread(img_path)
            if img is None:
                print(f"Failed to load image: {img_path}")
                return False
            
            original_shape = img.shape[:2]
            
            # 预处理
            input_data = self.preprocess_image(img)
            
            # 推理
            self.infer_request.set_input_tensor(input_data)
            self.infer_request.infer()
            
            # 获取输出
            output = self.infer_request.get_output_tensor().data
            
            # 后处理
            objects = self.postprocess(output, original_shape)
            
            # 转换为OneLabel格式
            target.clear()
            for obj in objects:
                if obj.conf >= 0.5:  # 最终置信度阈值
                    label = OneLabel(0)  # 灵活点数
                    for point in obj.points:
                        label.set_point_flexible(QPointF(point[0], point[1]))
                    label.set_class(obj.label)
                    target.append(label)
            
            return True
        
        except Exception as e:
            print(f"Detection error: {e}")
            return False