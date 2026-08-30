import cv2
import numpy as np
import os

def remove_watermark(image_path, watermark_path, exclusion_func, output_path = None):
    """
    核心去水印函数，通过传入一个函数来动态决定排除区域。
    """

    if not output_path:
        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_output_remove_watermark{ext}"

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
