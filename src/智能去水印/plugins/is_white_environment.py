import numpy as np

WHITE_THRESHOLD = 200

def is_white_environment(surround_pixels):
    """
    检测周围环境是否为白色
    逻辑：统计亮度大于 WHITE_THRESHOLD 的像素比例
    """
    if surround_pixels.size == 0:
        return False
        
    brightness = np.mean(surround_pixels, axis=-1)
    
    # 统计白色像素数量
    white_count = np.sum(brightness > WHITE_THRESHOLD)
    
    # 如果白色占比很高 (例如 > 50%)
    return (white_count / len(brightness)) > 0.5