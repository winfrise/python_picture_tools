import cv2
import numpy as np

def find_exclusion_mask(img, wm):
    """
    实现你指定的逻辑：找出高度在50-70px之间，且内部有规律小点点的横向区域。
    这个函数返回一个单通道的掩码图像，找到的区域为白色(255)，其余为黑色(0)。
    """
    # 创建一个和原图一样大的黑色画布，用来画我们的“排除区域”
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # --- 方案A：基于形态学特征 ---
    # 1. 转为灰度图，方便处理
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. 二值化，把小点点变成白色
    # 这里用OTSU自动找阈值，效果通常不错
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 3. 找轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 4. 筛选符合条件的轮廓
    candidate_rects = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # 条件1：高度在50-70px之间
        if 50 <= h <= 70:
            # 条件2：宽高比接近1，说明是“点”而不是长条
            if 0.5 < w / h < 2.0:
                candidate_rects.append((x, y, w, h))
    
    # 5. 将筛选出的“点”合并成一个大的矩形区域
    if candidate_rects:
        # 获取所有点的y坐标，找到它们集中的那一行
        y_coords = [y for x, y, w, h in candidate_rects]
        # 简单处理：取y坐标的众数（或平均值）作为基准线
        # 这里为了简化，我们直接找y坐标最密集的区域
        y_hist, y_bins = np.histogram(y_coords, bins=img.shape[0])
        if len(y_hist) > 0: # 防止没有点的情况
            main_y_bin = np.argmax(y_hist)
            target_y = int(y_bins[main_y_bin])
            
            # 再次筛选，只保留在这一行的点
            row_points = [p for p in candidate_rects if abs(p[1] - target_y) < 20] # 20px容差
            
            if len(row_points) >= 3: # 至少有3个点，才认为是“有规律”的
                # 找到这一行点的边界框
                x_coords = [x for x, y, w, h in row_points]
                x_coords_end = [x+w for x, y, w, h in row_points]
                min_x, max_x = min(x_coords), max(x_coords_end)
                min_y, max_y = min([y for x, y, w, h in row_points]), max([y+h for x, y, w, h in row_points])
                
                # 在掩码上画出这个矩形区域
                cv2.rectangle(mask, (min_x, min_y), (max_x, max_y), 255, -1)
                
    return mask
