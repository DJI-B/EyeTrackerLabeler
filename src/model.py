import cv2
import numpy as np
from typing import List, Tuple, Optional
from PyQt5.QtCore import QPointF
from .label_manager import OneLabel

# 尝试导入ONNX Runtime，如果失败则使用模拟版本
try:
    import onnxruntime as ort
    ONNXRUNTIME_AVAILABLE = True
except ImportError:
    ONNXRUNTIME_AVAILABLE = False
    print("Warning: ONNX Runtime not available. Smart detection will be disabled.")

class Object:
    """检测对象"""
    def __init__(self):
        self.conf = 0.0
        self.points: List[Tuple[float, float]] = []
        self.rect = (0, 0, 0, 0)  # x, y, w, h

class SmartAdd:
    """智能标注类"""
    
    def __init__(self):
        self.num_points = 7  # 固定为7个点
        self.model_path = ""
        self.input_width = 640
        self.input_height = 640
        self.conf_thresh = 0.6
        self.nms_thresh = 0.3
        
        # ONNX Runtime相关
        if ONNXRUNTIME_AVAILABLE:
            self.session = None
            self.input_name = None
            self.output_names = None
        else:
            self.session = None
    
    def set_num_points(self, points: int):
        """设置点数（固定为7，此方法保持兼容性）"""
        self.num_points = 7  # 始终为7个点
    
    def set_model(self, model_path: str) -> bool:
        """设置模型路径"""
        if not ONNXRUNTIME_AVAILABLE:
            print("ONNX Runtime not available")
            return False
        
        try:
            self.model_path = model_path
            
            # 创建ONNX Runtime会话
            providers = ['CPUExecutionProvider']
            if ort.get_device() == 'GPU':
                providers.insert(0, 'CUDAExecutionProvider')
            
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            
            # 获取输入输出信息
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            # 获取输入形状
            input_shape = self.session.get_inputs()[0].shape
            if len(input_shape) == 4:  # NCHW或NHWC
                if input_shape[1] == 3:  # NCHW
                    self.input_height = input_shape[2]
                    self.input_width = input_shape[3]
                else:  # NHWC
                    self.input_height = input_shape[1]
                    self.input_width = input_shape[2]
            
            print(f"Model loaded successfully. Input shape: {input_shape}")
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
        
        # 根据ONNX模型输出格式调整
        if isinstance(output, list):
            output = output[0]
        
        if output.ndim == 3:
            output = output[0]  # 移除batch维度
        
        # 假设输出格式为 [num_detections, conf + 7*2_points]
        # 即每个检测包含：置信度 + 7个点的x,y坐标
        expected_size = 1 + self.num_points * 2  # 1个置信度 + 7个点的坐标
        
        for detection in output:
            if len(detection) < expected_size:
                continue
            
            conf = detection[0]
            if conf < self.conf_thresh:
                continue
            
            obj = Object()
            obj.conf = conf
            
            # 提取点坐标
            scale_x = original_shape[1] / self.input_width
            scale_y = original_shape[0] / self.input_height
            
            for i in range(self.num_points):
                x_idx = 1 + i * 2
                y_idx = 1 + i * 2 + 1
                
                if y_idx < len(detection):
                    x = detection[x_idx] * scale_x
                    y = detection[y_idx] * scale_y
                    obj.points.append((x, y))
            
            if len(obj.points) == self.num_points:
                objects.append(obj)
        
        return objects
    
    def non_max_suppression(self, objects: List[Object]) -> List[Object]:
        """非极大值抑制"""
        if not objects:
            return objects
        
        # 简单的NMS实现
        objects.sort(key=lambda x: x.conf, reverse=True)
        
        keep = []
        for i, obj in enumerate(objects):
            should_keep = True
            for kept_obj in keep:
                # 计算IoU或距离，这里简化处理
                if self.calculate_overlap(obj, kept_obj) > self.nms_thresh:
                    should_keep = False
                    break
            
            if should_keep:
                keep.append(obj)
        
        return keep
    
    def calculate_overlap(self, obj1: Object, obj2: Object) -> float:
        """计算两个对象的重叠度"""
        if not obj1.points or not obj2.points:
            return 0.0
        
        # 简化计算：计算第一个点的距离
        p1 = obj1.points[0]
        p2 = obj2.points[0]
        
        distance = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
        
        # 归一化距离作为重叠度
        max_distance = 100  # 阈值
        return max(0, 1 - distance / max_distance)
    
    def detect(self, img_path: str, target: List[OneLabel]) -> bool:
        """检测函数"""
        if not ONNXRUNTIME_AVAILABLE or not self.session:
            print("Model not loaded or ONNX Runtime not available")
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
            outputs = self.session.run(self.output_names, {self.input_name: input_data})
            
            # 后处理
            objects = self.postprocess(outputs, original_shape)
            
            # NMS
            objects = self.non_max_suppression(objects)
            
            # 转换为OneLabel格式
            target.clear()
            for obj in objects:
                if obj.conf >= 0.5:  # 最终置信度阈值
                    label = OneLabel(self.num_points)
                    for point in obj.points:
                        label.set_point(QPointF(point[0], point[1]))
                    target.append(label)
            
            return True
        
        except Exception as e:
            print(f"Detection error: {e}")
            return False