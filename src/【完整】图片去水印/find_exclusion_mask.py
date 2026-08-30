import cv2
import numpy as np
import os

def find_exclusion_mask(image_path, watermark_path=None, debug_mode=False):
    """
    检测图片中的目标区域（优化版：增加原图二次校验以缩小高度）
    :param image_path: 图片路径
    :return: 包含检测到的区域坐标的列表 [(x, y, w, h), ...]，如果没有检测到则返回 []
    """
    # --- 参数配置 ---
    THRESHOLD = 240           # 判定为“暗色内容”的灰度阈值
    MIN_RECT_HEIGHT = 55      # 粗检测时的最小高度
    MAX_RECT_HEIGHT = 140     # 粗检测时的最大高度
    REFINED_MIN_HEIGHT = 20   # 精细修剪后允许的最小高度（防止误删）

    img = cv2.imread(image_path)
    if img is None:
        print("❌ 无法读取图片，请检查路径")
        return []

    detected_boxes = []
    
    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # --- 第一步：降采样 (宽度压到 800px) ---
    target_width = 800
    # 防止原图比800还小的情况
    if w > target_width:
        scale_ratio = w / target_width
        small_h = int(h / scale_ratio)
        small_gray = cv2.resize(gray, (target_width, small_h), interpolation=cv2.INTER_AREA)
    else:
        scale_ratio = 1.0
        small_gray = gray
        small_h = h

    # --- 第二步：分析缩略图的每一行 (粗定位) ---
    # 提取 ROI 区域：所有行，第 100 列 到 倒数第 50 列
    # 注意：原代码注释写的是-200，实际代码是-50，这里保持一致用-50
    roi = small_gray[:, 100:-50] 
    row_means = np.mean(roi, axis=1) # 计算水平投影均值

    # --- 第三步：寻找目标区域 (粗坐标) ---
    is_pattern_row = row_means < THRESHOLD
    in_region = False
    start_y = 0
    
    # 临时存储粗检测到的框
    rough_boxes = []

    for i, is_match in enumerate(is_pattern_row):
        if is_match and not in_region:
            start_y = i
            in_region = True
        elif not is_match and in_region:
            end_y = i
            in_region = False
            rough_boxes.append((start_y, end_y))
    
    # 处理图片底部截断的情况
    if in_region:
        rough_boxes.append((start_y, len(is_pattern_row)))

    # --- 第四步：坐标映射与二次精细校验 (核心优化点) ---
    final_boxes = []

    for (r_start_y, r_end_y) in rough_boxes:
        # 1. 映射回原图坐标
        raw_start_y = int(r_start_y * scale_ratio)
        raw_end_y = int(r_end_y * scale_ratio)
        raw_height = raw_end_y - raw_start_y

        # 2. 初步高度筛选 (沿用原逻辑)
        if not (MIN_RECT_HEIGHT < raw_height < MAX_RECT_HEIGHT):
            if debug_mode: print(f"❌ 高度不符(粗检): 实际 {raw_height}px")
            continue

        # 3. 【新增】在原图上重新检验并缩小区域
        # 为了防止越界，确保坐标在 0 到 h 之间
        safe_start = max(0, raw_start_y)
        safe_end = min(h, raw_end_y)
        
        # 截取原图对应的灰度区域
        # 这里我们只看中间部分的列，避免左右边缘干扰，或者看全宽
        crop_gray = gray[safe_start:safe_end, :]
        
        if crop_gray.size == 0: continue

        # 计算截取区域每一行的平均亮度
        crop_row_means = np.mean(crop_gray, axis=1)
        
        # 从上往下找：找到第一个“暗”像素的位置 (去除顶部空白)
        top_trim = 0
        for val in crop_row_means:
            if val < THRESHOLD:
                break
            top_trim += 1
            
        # 从下往上找：找到第一个“暗”像素的位置 (去除底部空白)
        bottom_trim = 0
        for val in reversed(crop_row_means):
            if val < THRESHOLD:
                break
            bottom_trim += 1
            
        # 计算修剪后的新坐标
        refined_start_y = safe_start + top_trim
        refined_end_y = safe_end - bottom_trim
        refined_height = refined_end_y - refined_start_y

        # 4. 最终校验：确保修剪后高度依然合理
        if refined_height >= REFINED_MIN_HEIGHT:
            box = (0, refined_start_y, w, refined_height)
            final_boxes.append(box)
            if debug_mode:
                print(f"✅ 发现有效区域: 原始高度[{raw_height}] -> 修剪后高度[{refined_height}] (Y: {refined_start_y}-{refined_end_y})")
        else:
            if debug_mode:
                print(f"⚠️ 修剪后高度过小被丢弃: {refined_height}px")

    # --- 第五步：保存结果 ---
    if len(final_boxes) > 0:
        print(f"\n🎉 检测完成！共找到 {len(final_boxes)} 个区域。")
        # 在图片上画框
        for box in final_boxes:
            x, y, bw, bh = box
            # 画红色矩形框，线宽2
            cv2.rectangle(img, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
        
        # 保存图片
        output_dir = os.path.dirname(image_path)
        output_name = os.path.join(output_dir, "result_detected.jpg")
        cv2.imwrite(output_name, img)
        print(f"💾 结果图片已保存至: {output_name}")
        return final_boxes
    else:
        print("\n😭 未找到任何匹配区域，图片未保存。")
        return []

