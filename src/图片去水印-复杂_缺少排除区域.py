import cv2
import numpy as np

def remove_watermark_with_exclusion(image_path, watermark_path, output_path, exclusion_func):
    """
    核心去水印函数，通过传入一个函数来动态决定排除区域。
    """
    # 1. 读取原图和白底水印图
    img = cv2.imread(image_path)
    wm = cv2.imread(watermark_path)
    if img is None or wm is None:
        raise ValueError("无法读取原图或水印图，请检查路径！")
    
    # 确保水印图与原图尺寸一致
    if img.shape != wm.shape:
        wm = cv2.resize(wm, (img.shape[1], img.shape[0]))

    # 2. 核心变化：调用传入的函数，获取排除区域的掩码
    # exclusion_func 会接收原图和水印图，并返回一个单通道的掩码图像
    exclusion_mask = exclusion_func(img, wm)

    # 3. 模拟 PS 的 Ctrl+I (反向)
    inverted_wm = cv2.bitwise_not(wm)

    # 4. 执行“线性减淡” (基色 + 混合色 = 结果色)
    result = cv2.add(img, inverted_wm)

    # 5. 应用排除区域掩码
    # 在掩码为白色(255)的区域，恢复原图的颜色
    # 注意：exclusion_mask 是单通道，需要增加一个维度才能和3通道的图片对齐
    final_result = np.where(exclusion_mask[:, :, np.newaxis] == 255, img, result)

    # 6. 保存结果
    cv2.imwrite(output_path, final_result)
    print(f"处理完成，已保存至: {output_path}")

    # --- 调试用：可视化排除区域 ---
    # 把找到的区域在原图上用半透明红色标出来，方便你确认找得准不准
    debug_img = img.copy()
    debug_img[exclusion_mask == 255] = (debug_img[exclusion_mask == 255] * 0.5 + np.array([0, 0, 255]) * 0.5).astype(np.uint8)
    cv2.imwrite("debug_exclusion_area.jpg", debug_img)
    print("已生成调试图 debug_exclusion_area.jpg，红色区域即为排除区域。")


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

# ================= 运行测试 =================
if __name__ == "__main__":
    # 调用时，直接把函数名传进去就行，不用加括号
    remove_watermark_with_exclusion(
        image_path="/Users/teacher/Desktop/test/page28_img1.png", 
        watermark_path="/Users/teacher/Desktop/test/mask.png", 
        output_path="/Users/teacher/Desktop/test/page28_img1_output2222.png",
        exclusion_func=find_exclusion_mask # 传入我们刚刚实现的函数
    )