import cv2
import numpy as np

def find_exclusion_mask(img, wm):
    """
    核心逻辑：找出高度在 50-70px 之间，且包含文字/横线的横向区域。
    """
    h, w = img.shape[:2]
    # 创建一个全白的掩码（白色=不去除，黑色=排除/保留原图）
    mask = np.ones((h, w), dtype=np.uint8) * 255 
    
    # 转灰度，方便统计像素
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 二值化：把文字和表格线变成白色(255)，背景变成黑色(0)
    # 这里的阈值 200 可以根据图片清晰度微调，目的是提取出所有的“墨迹”
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # 【关键步骤】水平投影：统计每一行有多少个“墨迹”像素
    # row_sum 是一个数组，长度等于图片高度 h
    row_sum = np.sum(binary, axis=1)

    # 遍历每一行，寻找符合条件的“行带”
    # 我们定义一个滑动窗口或者状态机来记录连续的行
    start_y = -1
    min_height = 50
    max_height = 70
    
    for y in range(h):
        # 如果这一行有明显的文字或线条（阈值设为宽度的 10%，防止噪点）
        if row_sum[y] > w * 0.1: 
            if start_y == -1:
                start_y = y  # 记录开始行
        else:
            # 如果断开了，检查刚才那段是不是我们要的
            if start_y != -1:
                current_height = y - start_y
                # 判断高度是否在 50-70px 之间
                if min_height <= current_height <= max_height:
                    # ✅ 找到了！在掩码上把这一块涂黑（0）
                    mask[start_y:y, :] = 0
                    print(f"找到排除区域: Y={start_y}, 高度={current_height}")
                
                # 重置起点
                start_y = -1
    
    # 处理最后一段可能没断开的情况
    if start_y != -1:
        current_height = h - start_y
        if min_height <= current_height <= max_height:
            mask[start_y:h, :] = 0
            
    return mask

def remove_watermark_with_logic(image_path, watermark_path, output_path):
    img = cv2.imread(image_path)
    wm = cv2.imread(watermark_path)
    
    if img is None or wm is None: raise ValueError("图片读取失败")
    if img.shape != wm.shape: wm = cv2.resize(wm, (img.shape[1], img.shape[0]))

    # 1. 获取排除掩码
    exclusion_mask = find_exclusion_mask(img, wm)

    # 2. 执行去水印逻辑 (线性减淡的反向操作)
    # 将水印反转
    inv_wm = cv2.bitwise_not(wm)
    
    # 混合计算 (模拟 PS 线性减淡)
    # 结果 = 原图 + 反色水印 - 255
    result = cv2.add(img.astype(np.int16), inv_wm.astype(np.int16)) - 255
    result = np.clip(result, 0, 255).astype(np.uint8)

    # 3. 【关键】应用掩码
    # 在掩码为黑色的地方（排除区），用原图覆盖掉处理后的结果
    # 意思是：这块区域我不去水印了，保持原样！
    result[exclusion_mask == 0] = img[exclusion_mask == 0]

    cv2.imwrite(output_path, result)
    print(f"处理完成，已保存至: {output_path}")

# --- 调用示例 ---
remove_watermark_with_logic(
        image_path="/Users/teacher/Desktop/test/page28_img1.png", 
        watermark_path="/Users/teacher/Desktop/test/mask.png", 
        output_path="/Users/teacher/Desktop/test/page28_img1_output2222.png",
)