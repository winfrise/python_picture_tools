import cv2
import numpy as np
import os 

def debug_detect(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("❌ 无法读取图片，请检查路径")
        return

    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # --- 第一步：降采样 (宽度压到 500px) ---
    target_width = 800
    scale_ratio = w / target_width
    small_h = int(h / scale_ratio)
    
    # 使用 INTER_AREA 进行缩小，这会让密集的点阵变成均匀的灰色
    small_gray = cv2.resize(gray, (target_width, small_h), interpolation=cv2.INTER_AREA)
    
    print(f"📏 原图尺寸: {w}x{h}, 缩放比例: {scale_ratio:.2f}")
    print(f"🔍 正在分析缩略图 (尺寸: {target_width}x{small_h})...")

    # --- 第二步：分析缩略图的每一行 ---
    # 我们计算每一行的平均像素值
    # 如果是白底黑点：空白行平均值接近 255，点阵行平均值会下降（比如变成 200 或更低）
    row_means = np.mean(small_gray, axis=1)

    # 打印前几行和中间几行的数值，看看“点阵区”到底是多少分
    print(f"📊 缩略图第1行平均亮度: {row_means[0]:.1f}")
    print(f"📊 缩略图中间行平均亮度: {row_means[small_h//2]:.1f}")
    
    # --- 第三步：寻找目标区域 (调试模式) ---
    # 假设：我们要找亮度明显低于背景（255）的区域
    # 这里的阈值 240 是个保守值，意味着只要稍微有点黑就算
    threshold = 240 
    is_pattern_row = row_means < threshold 
    
    # 找出连续为 True 的片段
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
            
            # 计算原图的高度
            raw_height = (end_y - start_y) * scale_ratio
            
            # 打印每一个检测到的块，不管高度是否符合，先看看
            print(f"👉 发现疑似区域: 缩略图Y[{start_y}-{end_y}], "
                  f"对应原图高度约: {raw_height:.0f}px, "
                  f"平均亮度: {np.mean(row_means[start_y:end_y]):.1f}")
            
            if 40 < raw_height < 100: # 放宽高度限制看看
                print(f"   ✅ 符合高度要求！")
                found_count += 1
                
                # 在原图上画框
                # 注意：这里只是画个大概，因为我们是按行扫描的
                pt1 = (0, int(start_y * scale_ratio))
                pt2 = (w, int(end_y * scale_ratio))

                # 一、框选
                cv2.rectangle(img, pt1, pt2, (0, 0, 255), 2)

                # 二、使用选区
                # overlay = img.copy()
                # cv2.rectangle(overlay, pt1, pt2, (0, 0, 255), -1)
                # alpha = 0.3 
                # cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


            else:
                print(f"   ❌ 高度不符 (要求50-80px)")

    if found_count > 0:
        # 获取原图所在的文件夹路径
        output_dir = os.path.dirname(image_path)
        # 拼接生成新的保存路径 (例如: C:/Images/result_debug.jpg)
        output_name = os.path.join(output_dir, "result_debug.jpg")
        cv2.imwrite(output_name, img)
        print(f"\n🎉 处理完成！已保存结果到: {output_name}")
    else:
        print("\n😭 依然未找到完美匹配的区域，请查看上面的打印数据分析原因。")

# 使用你的图片路径运行
# 请确保把下面的路径换成你真实的图片路径
debug_detect("/Users/teacher/Desktop/test/test.png") 
