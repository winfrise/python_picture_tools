import numpy as np

DARK_THRESHOLD_MIN = 0
DARK_THRESHOLD_MAX = 150

def is_dark_environment(surround_pixels):
    """
    检测周围环境是否为深色
    逻辑：统计亮度在 [0, 150] 之间的像素比例
    """
    if surround_pixels.size == 0:
        return False
    
    # 计算灰度/亮度 (简单的平均值或取单通道)
    # 假设是 RGB 图，计算平均亮度
    brightness = np.mean(surround_pixels, axis=-1) 
    
    # 统计深色像素数量
    dark_count = np.sum((brightness >= DARK_THRESHOLD_MIN) & (brightness <= DARK_THRESHOLD_MAX))
    
    # 如果深色占比超过 50% (可调整)，则认为是深色环境
    # 注意：这里需要根据你的原代码逻辑确认比例阈值，通常是 > 0.5
    return (dark_count / len(brightness)) > 0.5 