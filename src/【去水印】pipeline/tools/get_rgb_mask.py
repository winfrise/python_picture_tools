import cv2
import numpy as np

def rgb_to_hsv_range(rgb_color, h_threshold=5, s_threshold=5, v_threshold=5):
    """
    将 RGB 颜色转换为 OpenCV 的 HSV 范围 (上下浮动)
    
    :param rgb_color: list/tuple, [R, G, B] (0-255)
    :param h_tolerance: int, H值上下浮动的范围 (OpenCV中H最大180，通常取5-10)
    :param s_tolerance: int, S值上下浮动的范围 (0-255)
    :param v_tolerance: int, V值上下浮动的范围 (0-255)
    :return: (lower_hsv, upper_hsv) numpy arrays
    """
    # 1. 创建单像素图像并转换颜色空间
    # OpenCV 是 BGR 格式，所以输入要反转
    pixel = np.uint8([[rgb_color[::-1]]]) 
    hsv_pixel = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)
    
    h, s, v = hsv_pixel[0][0]
    
    # 2. 计算下限 (Lower Bound)
    lower_h = max(h - h_threshold, 0)
    lower_s = max(s - s_threshold, 0)
    lower_v = max(v - v_threshold, 0)
    
    # 3. 计算上限 (Upper Bound)
    # 注意：OpenCV 的 H 范围是 0-180
    upper_h = min(h + h_threshold, 180)
    upper_s = min(s + s_threshold, 255)
    upper_v = min(v + v_threshold, 255)
    
    return np.array([lower_h, lower_s, lower_v]), np.array([upper_h, upper_s, upper_v])

def get_rgb_mask(img, color_rgb_list):

    # 1. 将整张图转为 HSV (只需做一次，效率高)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = hsv_img.shape[:2]
    
    # 初始化一个全黑的掩膜（作为合并的基础）
    # 逻辑：我们需要找出所有“符合排除条件”的像素，最后取反即可
    final_exclude_mask = np.zeros((h, w), dtype=np.uint8)

    for item in color_rgb_list:
        color_rgb =  item.get('color_rgb')
        h_threshold = item.get('h_threshold', 10)
        s_threshold = item.get('s_threshold', 10)
        v_threshold = item.get('v_threshold', 10)

        # 获取该颜色的 HSV 范围
        lower_hsv, upper_hsv = rgb_to_hsv_range(
            color_rgb, 
            h_threshold=h_threshold,
            s_threshold=s_threshold,
            v_threshold=v_threshold
        )
        
        # 生成当前颜色的掩膜
        single_mask = cv2.inRange(hsv_img, lower_hsv, upper_hsv)
        
        # 合并掩膜 (只要满足任意一种颜色，就标记为白色)
        final_exclude_mask = cv2.bitwise_or(final_exclude_mask, single_mask)


    mask_to_save = final_exclude_mask.astype(np.uint8) 

    # 保存为 PNG 格式（强烈推荐！）
    cv2.imwrite("watermark_mask.png", mask_to_save)
    return final_exclude_mask
