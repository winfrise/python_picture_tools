
import numpy as np

FILL_COLOR = [255, 255, 255]
FILL_COLOR = [0, 255, 0]

def fill_watermark_white(img, final_mask):
    """
    将水印区域填充为白色。
    
    参数:
        img: 原始图像 (numpy array, shape: H x W x C)
        final_mask: 水印区域掩码 (numpy array, shape: H x W), 非零值表示水印区域
    
    返回:
        填充后的图像
    """
    result = img.copy()
    
    # 获取所有需要填充的水印像素坐标
    ys, xs = np.where(final_mask > 0)
    
    for y, x in zip(ys, xs):
        result[y, x] = FILL_COLOR
    
    return result