import cv2
import numpy as np
import os


def find_exclusion_mask(image_path, debug_mode = False):
    """
    检测图片中的目标区域。
    :param image_path: 图片路径
    :return: 包含检测到的区域坐标的列表 [(x, y, w, h), ...]，如果没有检测到则返回 []
    """
    img = cv2.imread(image_path)
    if img is None:
        print("❌ 无法读取图片，请检查路径")
        return []

    # 用于存储最终结果的列表
    detected_boxes = []

    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # --- 第一步：降采样 (宽度压到 800px) ---
    target_width = 800
    scale_ratio = w / target_width
    small_h = int(h / scale_ratio)
    small_gray = cv2.resize(gray, (target_width, small_h), interpolation=cv2.INTER_AREA)

    # --- 第二步：分析缩略图的每一行 ---
    row_means = np.mean(small_gray, axis=1)

    # --- 第三步：寻找目标区域 ---
    threshold = 240
    is_pattern_row = row_means < threshold
    in_region = False
    start_y = 0

    for i, is_match in enumerate(is_pattern_row):
        if is_match and not in_region:
            start_y = i
            in_region = True
        elif not is_match and in_region:
            end_y = i
            in_region = False
            
            # 计算原图的高度和坐标
            raw_start_y = int(start_y * scale_ratio)
            raw_end_y = int(end_y * scale_ratio)
            raw_height = raw_end_y - raw_start_y

            # 1. 先过高度筛选
            if 40 < raw_height < 150:
                # 2. 再过二次纹理密度筛选
                # 注意：这里x设为0，w设为全宽
                box = (0, raw_start_y, w, raw_height)
                

                print(f"✅ 发现有效区域: Y[{raw_start_y}-{raw_end_y}], 高度: {raw_height}")
                detected_boxes.append(box)
            else:
                print(f"❌ 高度不符 (要求40-150px): 实际 {raw_height}px")

    # 循环结束后，如果还在区域内，需要处理最后一段（防止图片底部截断）
    if in_region:
         end_y = len(is_pattern_row)
         raw_start_y = int(start_y * scale_ratio)
         raw_end_y = int(end_y * scale_ratio)
         raw_height = raw_end_y - raw_start_y
         if 40 < raw_height < 150:
            box = (0, raw_start_y, w, raw_height)
            detected_boxes.append(box)



    if debug_mode:
        print(f"\n🎉 检测完成！共找到 {len(detected_boxes)} 个区域。")
        
        # 2. 在图片上画框 (保存图片的功能放在这里)
        for box in detected_boxes:
            x, y, w, h = box
            # 画红色矩形框，线宽2
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
        # 3. 保存图片
        output_dir = os.path.dirname(image_path)
        output_name = os.path.join(output_dir, "result_detected.jpg")
        cv2.imwrite(output_name, img)
        print(f"💾 结果图片已保存至: {output_name}")
        
    else:
        print("\n😭 未找到任何匹配区域，图片未保存。")


    return detected_boxes

