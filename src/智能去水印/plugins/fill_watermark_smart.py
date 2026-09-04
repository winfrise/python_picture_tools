import numpy as np
from .get_surround_pixels import get_surround_pixels
from .is_dark_environment import is_dark_environment
from .is_white_environment import is_white_environment

SURROUND_RADIUS = 5

def fill_watermark_smart(img, final_mask):
    result_img = img.copy()
    ys, xs = np.where(final_mask > 0)

    for y, x in zip(ys, xs):
        # 1. 获取周围邻域的掩码情况
        region_mask = get_surround_pixels(final_mask, y, x, SURROUND_RADIUS)
        
        # 找出周围属于"背景"（非水印）的坐标
        bg_coords = np.where(region_mask == 0)
        
        # 如果没有背景像素（被水印包围），直接填白
        if len(bg_coords[0]) == 0:
            result_img[y, x] = [255, 255, 255]
            continue
            
        # 获取周围背景的实际像素颜色值
        # 注意：这里需要利用 bg_coords 从原图中取值
        # 为了性能，通常建议直接传切片给检测函数，这里简化演示逻辑
        region_img = img[
            max(0, y-SURROUND_RADIUS):min(img.shape[0], y+SURROUND_RADIUS+1),
            max(0, x-SURROUND_RADIUS):min(img.shape[1], x+SURROUND_RADIUS+1)
        ]
        surround_pixels = region_img[bg_coords]

        # 2. 调用抽离出的检测函数
        
        # 优先判断深色环境
        if is_dark_environment(surround_pixels):
            result_img[y, x] = [255, 255, 255]
            
        # 判断白色环境
        elif is_white_environment(surround_pixels):
            result_img[y, x] = [255, 255, 255]
            
        # 其他情况（例如彩色环境，使用原来的多数投票逻辑）
        else:
            # 否则，找周围出现最多的颜色

            # 颜色量化，让直方图统计更稳定（每32个颜色值合并为一个桶）
            quantized_img = (img // 32) * 32
            

            pass 
            
    return result_img