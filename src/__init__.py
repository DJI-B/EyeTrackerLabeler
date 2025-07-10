# src/__init__.py
"""
Helios Label Tool - Python版本
一个功能完整的图像标注工具

主要组件:
- MainWindow: 主界面
- DrawOnPic: 图像显示和标注组件
- AllLabel: 标签数据管理
- OneLabel: 单个标签管理
- Painter: 图像绘制器
- SmartAdd: AI智能检测
"""

__version__ = "1.0.0"
__author__ = "Helios Label Tool Team"
__email__ = "support@helios-label.com"

# 导入主要类，方便外部使用
from .main_window import MainWindow
from .draw_on_pic import DrawOnPic
from .label_manager import OneLabel
from .txt_manager import AllLabel
from .qt_painter import Painter
from .model import SmartAdd
from .index_list import IndexQListWidgetItem

# 定义公共API
__all__ = [
    'MainWindow',
    'DrawOnPic', 
    'OneLabel',
    'AllLabel',
    'Painter',
    'SmartAdd',
    'IndexQListWidgetItem',
    # 常量
    'MOVE',
    'ADD',
    'ARMOR',
    'ENERGY', 
    'NORM',
]

# 导入常量
from .draw_on_pic import MOVE, ADD, ARMOR, ENERGY, NORM

# 可选：添加包级别的配置
DEFAULT_CONFIG = {
    'default_num_points': 4,
    'default_conf_thresh': 0.6,
    'default_nms_thresh': 0.3,
    'supported_image_formats': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
    'supported_model_formats': ['.onnx'],
}

def get_version():
    """获取版本信息"""
    return __version__

def get_config():
    """获取默认配置"""
    return DEFAULT_CONFIG.copy()

# 可选：添加包初始化逻辑
def _check_dependencies():
    """检查依赖是否满足"""
    missing_deps = []
    
    try:
        import PyQt5
    except ImportError:
        missing_deps.append('PyQt5')
    
    try:
        import cv2
    except ImportError:
        missing_deps.append('opencv-python')
    
    try:
        import numpy
    except ImportError:
        missing_deps.append('numpy')
    
    # OpenVINO是可选的
    try:
        import openvino
    except ImportError:
        import warnings
        warnings.warn("OpenVINO not found. Smart detection will be disabled.", 
                     UserWarning)
    
    if missing_deps:
        raise ImportError(f"Missing required dependencies: {', '.join(missing_deps)}")

# 在包导入时检查依赖
_check_dependencies()

# 包级别的日志配置
import logging

def setup_logging(level=logging.INFO):
    """设置日志配置"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('helios_label.log')
        ]
    )

# 创建包级别的日志器
logger = logging.getLogger(__name__)
logger.info(f"Helios Label Tool v{__version__} initialized")