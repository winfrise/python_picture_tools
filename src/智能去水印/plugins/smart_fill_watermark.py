import numpy as np
from collections import Counter

SURROUND_RADIUS = 5                   #向外采样扩展的半径
WHITE_THRESHOLD = 200                 #填充白色的亮度判定阈值

DARK_THRESHOLD_MIN = 0 #（深色阈值下限）
DARK_THRESHOLD_MAX = 150 #（深色阈值上限）
IS_DARK_SURROUND_FILL_WHITE = True # 是否开启黑色填充白色）

def smart_fill_watermark(
        img, 
        final_mask, 
        surround_radius=SURROUND_RADIUS, 
        white_threshold=WHITE_THRESHOLD, 
        dark_threshold_min=DARK_THRESHOLD_MIN, 
        dark_threshold_max = DARK_THRESHOLD_MAX,
        is_dark_surround_fill_white=IS_DARK_SURROUND_FILL_WHITE
):
    """
    智能填充水印区域。
    根据水印周围的像素颜色，决定填充为白色还是周围最多的颜色。
    如果开启了 is_dark_surround_fill_white 且周围接近黑色较多，则强制填充白色。
    """
    result = img.copy()
    img_h, img_w = img.shape[:2]
    
    # 颜色量化，让直方图统计更稳定（每32个颜色值合并为一个桶）
    quantized_img = (img // 32) * 32
    
    # 获取所有需要填充的水印像素坐标
    ys, xs = np.where(final_mask > 0)
    
    # 记录哪些位置是因为黑色被填充的（用于调试图）
    dark_fill_mask = np.zeros((img_h, img_w), dtype=np.uint8)
    
    for y, x in zip(ys, xs):
        # 计算采样窗口边界
        y_min = max(0, y - surround_radius)
        y_max = min(img_h, y + surround_radius + 1)
        x_min = max(0, x - surround_radius)
        x_max = min(img_w, x + surround_radius + 1)
        
        # 提取周围区域
        surround_patch = img[y_min:y_max, x_min:x_max]
        surround_mask_patch = final_mask[y_min:y_max, x_min:x_max]
        
        # 只取非水印区域的像素作为背景参考
        valid_pixels = surround_patch[surround_mask_patch == 0]
        
        if valid_pixels.size == 0:
            # 如果周围全是水印，默认填白色
            result[y, x] = [255, 255, 255]
            continue
            
        # 判断周围是否有超过一半是接近黑色的
        if is_dark_surround_fill_white:
            is_dark_max = np.all(valid_pixels <= dark_threshold_max, axis=1)
            is_dark_min = np.all(valid_pixels >= dark_threshold_min, axis=1)
            is_dark = is_dark_max & is_dark_min
            dark_ratio = np.sum(is_dark) / len(is_dark)
            if dark_ratio > 0.5:
                result[y, x] = [255, 255, 255]
                dark_fill_mask[y, x] = 255
                continue
        
        # 判断周围是否有超过一半是接近白色的
        is_white = np.all(valid_pixels > white_threshold, axis=1)
        white_ratio = np.sum(is_white) / len(is_white)
        
        if white_ratio > 0.5:
            # 周围主要是白色，填充白色
            result[y, x] = [255, 255, 255]
        else:
            # 否则，找周围出现最多的颜色
            quantized_patch = quantized_img[y_min:y_max, x_min:x_max]
            valid_quantized = quantized_patch[surround_mask_patch == 0]
            
            if valid_quantized.size == 0:
                result[y, x] = [255, 255, 255]
                continue
                
            # 将颜色转为元组以便统计
            colors = [tuple(c) for c in valid_quantized]
            most_common_color = Counter(colors).most_common(1)[0][0]
            
            # 用原始图像中该颜色组的平均值填充（更平滑）
            color_mask = np.all(valid_quantized == most_common_color, axis=1)
            avg_color = np.mean(valid_pixels[color_mask], axis=0).astype(np.uint8)
            
            result[y, x] = avg_color
            
    return result

