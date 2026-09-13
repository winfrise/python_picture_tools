import cv2
import numpy as np

def get_rgb_mask(img, color_rgb_list):

    # 1. 预处理图片：转为 float32 防止计算溢出，只需做一次
    img_float = img.astype(np.float32)
    h, w = img.shape[:2]
    
    # 初始化一个全黑的掩膜（作为合并的基础）
    # 逻辑：我们需要找出所有“符合排除条件”的像素，最后取反即可
    final_exclude_mask = np.zeros((h, w), dtype=np.uint8)

    for item in color_rgb_list:
        color_rgb =  item.get('color_rgb')
        color_threshold = item.get('color_threshold', 10)

        color_bgr = color_rgb[::-1]

        # 2. 【颜色排除】计算图片中每个像素与“目标绿色”的距离
        # 将图片转为 float32 以防止计算溢出
        target_color = np.array(color_bgr, dtype=np.float32)
        
        # 计算欧氏距离 (颜色差异)
        # 距离越小，说明越接近这个绿色
        color_dist = np.sqrt(np.sum((img_float - target_color)**2, axis=2))
        
        # C. 生成当前颜色的排除掩膜 (距离 < 阈值 -> 白色)
        single_exclude_mask = (color_dist < color_threshold).astype(np.uint8) * 255
        
        # D. 合并掩膜 (使用按位或运算：只要满足任意一种颜色，就标记为白色)
        final_exclude_mask = cv2.bitwise_or(final_exclude_mask, single_exclude_mask)




    # 3. 取反得到最终的 Keep Mask
    # 排除掩膜中白色是要删掉的 -> 取反后白色变成黑色(删掉)，黑色变成白色(保留)
    keep_mask = cv2.bitwise_not(final_exclude_mask)

    return keep_mask
