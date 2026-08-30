import cv2
import numpy as np
import os

def check_texture_density(image, box, white_threshold=250):
    """
    二次过滤核心逻辑：
    1. 将区域横向切成10列。
    2. 去掉第1个和最后1个（只看中间8列）。
    3. 只要这中间8列里，有任何一列的背景是“纯白”的，就不保留该区域。
    
    :param image: 原图 (BGR格式)
    :param box: 候选框 (x, y, w, h)
    :param white_threshold: 纯白阈值。大于此值即判定为“纯白”。
    :return: True 表示保留(是数据表)，False 表示过滤掉(是标题栏)
    """
    x, y, w, h = box
    
    # 1. 安全截取区域
    h_img, w_img = image.shape[:2]
    x, y = max(0, x), max(0, y)
    w = min(w, w_img - x)
    h = min(h, h_img - y)
    if w <= 10 or h <= 0: return False

    roi = image[y:y+h, x:x+w]
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 2. 将区域横向切成10列
    num_cols = 10
    col_width = w // num_cols
    if col_width == 0: return True 

    # 3. 检查中间的8列 (索引 1 到 8)
    for i in range(1, 9):
        col_start = i * col_width
        col_end = (i + 1) * col_width
        # 截取当前列
        col_strip = gray_roi[:, col_start:col_end]
        
        # 计算这一列的平均亮度
        mean_brightness = np.mean(col_strip)
        
        # 4. 核心判断：只要有任何一列是“纯白”的，直接过滤掉（返回 False）
        if mean_brightness > white_threshold:
            # print(f"   [二次过滤] 第 {i+1} 列亮度为 {mean_brightness:.1f}，判定为纯白，过滤该区域。")
            return False
            
    # 如果中间8列全都不够白（都有内容），则保留该区域
    # print(f"   [二次过滤] 中间8列均有内容，保留该区域。")
    return True

def debug_detect(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("❌ 无法读取图片，请检查路径")
        return

    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # --- 第一步：降采样 (宽度压到 800px) ---
    target_width = 800
    scale_ratio = w / target_width
    small_h = int(h / scale_ratio)
    
    small_gray = cv2.resize(gray, (target_width, small_h), interpolation=cv2.INTER_AREA)
    
    print(f"📏 原图尺寸: {w}x{h}, 缩放比例: {scale_ratio:.2f}")
    print(f"🔍 正在分析缩略图 (尺寸: {target_width}x{small_h})...")

    # --- 第二步：分析缩略图的每一行 ---
    row_means = np.mean(small_gray, axis=1)
    
    # --- 第三步：寻找目标区域 ---
    threshold = 240
    is_pattern_row = row_means < threshold
    
    in_region = False
    start_y = 0
    found_count = 0

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
            
            print(f"👉 发现疑似区域: 缩略图Y[{start_y}-{end_y}], "
                  f"对应原图高度约: {raw_height:.0f}px, "
                  f"平均亮度: {np.mean(row_means[start_y:end_y]):.1f}")

            # 1. 先过高度筛选
            if 40 < raw_height < 150: 
                # 2. 再过二次纹理密度筛选
                box = (0, raw_start_y, w, raw_height)
                
                # 这里的 white_threshold 设为 250，你可以根据效果调整
                if check_texture_density(img, box, white_threshold=250):
                    print(f"   ✅ 通过二次过滤！保留该区域。")
                    found_count += 1
                    # 在原图上画框
                    pt1 = (0, raw_start_y)
                    pt2 = (w, raw_end_y)
                    cv2.rectangle(img, pt1, pt2, (0, 0, 255), 2)
                else:
                    print(f"   ❌ 二次过滤拦截：中间区域存在纯白列（可能是标题栏）。")
            else:
                print(f"   ❌ 高度不符 (要求40-150px)。")

    if found_count > 0:
        output_dir = os.path.dirname(image_path)
        output_name = os.path.join(output_dir, "result_debug_v4.jpg")
        cv2.imwrite(output_name, img)
        print(f"\n🎉 处理完成！找到 {found_count} 个有效区域，已保存结果到: {output_name}")
    else:
        print("\n😭 未找到完美匹配的区域，请查看上面的打印数据分析原因。")

# 使用你的图片路径运行
debug_detect("/Users/teacher/Desktop/test/test.png")