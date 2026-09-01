import cv2
import numpy as np
import os
from utils import batch_process_file_with_callback

def remove_watermark_with_exclusion(image_path, watermark_path, output_path, 
                                    exclude_color_bgr, exclude_threshold=30):
    """
    基于线性减淡原理去水印，并排除特定颜色的矩形区域
    """
    # 1. 读取原图和白底水印图
    img = cv2.imread(image_path)
    wm = cv2.imread(watermark_path)
    
    if img is None or wm is None:
        raise ValueError("无法读取原图或水印图，请检查路径！")
    
    # 确保水印图与原图尺寸一致（如果不一致，需要调整水印大小）
    if img.shape != wm.shape:
        wm = cv2.resize(wm, (img.shape[1], img.shape[0]))

    # 2. 模拟 PS 的 Ctrl+I (反向)
    inverted_wm = cv2.bitwise_not(wm)

    # 3. 生成排除区域的掩码 (Mask)
    # 将原图转换为灰度或直接在 BGR 空间下寻找特定颜色
    # 假设你要排除的颜色是特定的，这里使用 cv2.inRange 提取该颜色区域
    lower_bound = np.array([max(0, c - exclude_threshold) for c in exclude_color_bgr])
    upper_bound = np.array([min(255, c + exclude_threshold) for c in exclude_color_bgr])
    
    # 创建掩码：匹配到的颜色区域为白色(255)，其他为黑色(0)
    color_mask = cv2.inRange(img, lower_bound, upper_bound)
    
    # 可选：对掩码进行形态学操作，把“小点点”连成一个完整的矩形块
    kernel = np.ones((5, 5), np.uint8)
    color_mask = cv2.dilate(color_mask, kernel, iterations=2)

    # 4. 执行“线性减淡” (基色 + 混合色 = 结果色)
    # 注意：结果不能超过 255，所以使用 cv2.add
    result = cv2.add(img, inverted_wm)

    # 5. 应用排除区域掩码
    # 在掩码为白色(255)的区域，恢复原图的颜色，不进行去水印操作
    # 使用 np.where 或 cv2.bitwise_and 均可，这里用 np.where 最直观
    final_result = np.where(color_mask[:, :, np.newaxis] == 255, img, result)

    # 6. 保存结果
    cv2.imwrite(output_path, final_result)
    print(f"处理完成，已保存至: {output_path}")

# ================= 运行测试 =================
if __name__ == "__main__":
    # 参数配置示例
    # 假设你要排除的区域是纯蓝色 (BGR格式: 255, 0, 0)
    TARGET_EXCLUDE_COLOR = (0, 0, 0) 

    input_path="/Users/teacher/Desktop/20260830/xx/111/xx"
    watermark_path="/Users/teacher/Desktop/20260830/xx/111/mask.jpg"
    
    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_去水印_线性渐变{ext}"
        remove_watermark_with_exclusion(
            image_path=input_path, 
            watermark_path=watermark_path, 
            output_path=output_path,
            exclude_color_bgr=TARGET_EXCLUDE_COLOR
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            remove_watermark_with_exclusion(
                image_path=input_file, 
                watermark_path=watermark_path, 
                output_path=output_file,
                exclude_color_bgr=TARGET_EXCLUDE_COLOR
            )

        output_dir = f'{input_path}_output_去水印_线性渐变'
        batch_process_file_with_callback(
            input_dir=input_path,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效")