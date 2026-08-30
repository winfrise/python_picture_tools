import cv2
import numpy as np
import os
import shutil

def check_texture_density(image, box, white_threshold=250):
    """
    二次过滤核心逻辑：
    1. 将区域横向切成10列。
    2. 去掉第1个和最后1个（只看中间8列）。
    3. 只要这中间8列里，有任何一列的背景是“纯白”的，就不保留该区域。
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
            return False
            
    # 如果中间8列全都不够白（都有内容），则保留该区域
    return True

def process_single_image(image_path, output_path=None):
    """
    处理单张图片的逻辑
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ 无法读取图片: {image_path}")
        return 0

    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # --- 第一步：降采样 (宽度压到 800px) ---
    target_width = 800
    scale_ratio = w / target_width
    small_h = int(h / scale_ratio)
    
    # 防止图片本身就很小，导致缩放出错
    if small_h <= 0:
        small_h = 1
        scale_ratio = 1

    small_gray = cv2.resize(gray, (target_width, small_h), interpolation=cv2.INTER_AREA)
    
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
            
            # 1. 先过高度筛选
            if 40 < raw_height < 150: 
                # 2. 再过二次纹理密度筛选
                box = (0, raw_start_y, w, raw_height)
                
                if check_texture_density(img, box, white_threshold=250):
                    found_count += 1
                    # 在原图上画框
                    pt1 = (0, raw_start_y)
                    pt2 = (w, raw_end_y)
                    cv2.rectangle(img, pt1, pt2, (0, 0, 255), 2)
            
    # 保存图片
    if found_count > 0:
        # 确定输出路径
        if not output_path:
            # 如果未指定，保存在原目录，文件名加前缀
            output_dir = os.path.dirname(image_path)
            base_name = os.path.basename(image_path)
            output_path = os.path.join(output_dir, f"{base_name}_output_result.jpg")
    
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_dir), exist_ok=True)
        
        cv2.imwrite(output_path, img)
        print(f"✅ 处理完成: {image_path} -> 找到 {found_count} 个区域, 保存至: {output_path}")
        return found_count
    else:
        cv2.imwrite(output_path, img)
        print(f"⚠️ 处理完成: {image_path} -> 未找到区域, 已保存原图。")        
        return 0

def process_folder(input_dir, output_dir = None):
    """
    批量处理文件夹内的图片，保持目录结构
    """
    # 支持的图片格式

    extensions = ('.jpg', '.jpeg', '.png', '.bmp')

    if not output_dir:
        output_dir = f"{input_dir}_output_result"

    os.makedirs(output_dir, exist_ok=True)


    print(f"📂 开始扫描输入目录: {input_dir}")
    
    total_files = 0
    total_found = 0
    
    # os.walk 会遍历所有子目录
    for root, dirs, files in os.walk(input_dir):
        # 过滤出图片文件
        image_files = [f for f in files if f.lower().endswith(extensions)]
        
        if not image_files:
            continue

        # 计算相对于输入目录的相对路径，用于在输出目录重建结构
        rel_path = os.path.relpath(root, input_dir)
        current_output_dir = os.path.join(output_dir, rel_path)
        
        # 确保输出目录的子文件夹存在
        if not os.path.exists(current_output_dir):
            os.makedirs(current_output_dir)

        for file in image_files:
            input_file_path = os.path.join(root, file)
            output_file_path = os.path.join(current_output_dir, file) # 文件名不变
            
            count = process_single_image(input_file_path, output_file_path)
            total_files += 1
            total_found += count
        
    print(f"\n🎉 批量处理结束！共处理 {total_files} 张图片，总共找到 {total_found} 个有效区域。")
    print(f"所有结果已保存至: {output_dir}")

# ================= 主程序入口 =================
if __name__ == "__main__":
    # 在这里修改你的路径
    
    # --- 批量处理模式 ---
    input_path = r"/Users/teacher/Desktop/test/test"       # 输入文件夹路径
    
    if os.path.isdir(input_path):
        # 如果是文件夹，执行批量处理
        process_folder(input_path)
    elif os.path.isfile(input_path):
        process_single_image(input_path)
    else:
        print("❌ 路径无效")