import numpy as np
from typing import List, Dict, Any, Callable
import time
import cv2
import os

from tools.fill_watermark_with_color import fill_watermark_with_color
from tools.get_rgb_mask import get_rgb_mask
from tools.detect_shape_mask import detect_shape_mask
from tools.get_watermark_img_mask import get_watermark_img_mask
from tools.get_gray_mask import get_gray_mask


def run_watermark_pipeline(image_path, steps, output_path = None):
    """
    纯函数流水线引擎 (扁平化参数版)
    """
    start_time = time.time()

    print(f"--正在处理图片:{image_path}")

    current_image = cv2.imread(image_path)

    for step in steps:
        watermark_area_img = step.get("watermark_area_img")
        target_gray = step.get("target_gray")
        target_gray_threshold = step.get("target_gray_threshold")
        exclude_rgb_list = step.get("exclude_rgb_list")
        include_rgb_list = step.get("include_rgb_list")
        expand_px = step.get("expand_px", 0)
        fill_color = step.get("fill_color")
        detect_shape_img = step.get("detect_shape_img")

        # 初始化 area_mask（默认整图都算水印区域）
        h, w = current_image.shape[:2]
        mask = np.ones((h, w), dtype=np.uint8) * 255

        # 获取水印大致区域
        if watermark_area_img:
            watermark_img_mask = get_watermark_img_mask(
                img = current_image, 
                mask = mask, 
                watermark_area_img = watermark_area_img
            )
            mask = cv2.bitwise_and(mask, watermark_img_mask)
        cv2.imwrite('111.png', mask)
        # 处理灰度区域范围
        if target_gray:
            gray_mask = get_gray_mask(
                img = current_image, 
                mask = mask,
                gray_range= [
                    target_gray - target_gray_threshold, 
                    target_gray + target_gray_threshold
                ]
            )
            mask = cv2.bitwise_and(mask, gray_mask)
        cv2.imwrite('1112.png', mask)
        # 形状检测
        if detect_shape_img:
            if not watermark_area_img:
                print('【错误】使用detect_shape_img功能时,请确定设置了[water_area_img]')
                return
            
            detect_mask = detect_shape_mask(
                img=current_image,
                mask = watermark_img_mask,
                detect_shape_img = detect_shape_img,
            )

            mask = cv2.bitwise_and(mask, detect_mask)

        # 包含的rgb颜色
        if include_rgb_list:
            if not watermark_area_img:
                print('【错误】使用include_rgb_list功能时,请确定设置了[water_area_img]')
                return
        
            mask_include = get_rgb_mask(
                img = current_image, 
                mask = watermark_img_mask,
                color_rgb_list=include_rgb_list
            )

            mask = cv2.bitwise_or(mask, mask_include)

        # 排除指定颜色的rgb蒙版
        if exclude_rgb_list:
            if not watermark_area_img:
                print('【错误】使用exclude_rgb_list功能时,请确定设置了[water_area_img]')
                return

            mask_exclude = get_rgb_mask(
                img = current_image, 
                mask = watermark_img_mask,
                color_rgb_list=exclude_rgb_list
            )
            # 1. 先对排除蒙版取反 (黑色变白，白色变黑)
            # 此时，你想排除的区域变成了 0 (黑)，其他区域是 255 (白)
            mask_exclude_inv = cv2.bitwise_not(mask_exclude)

            # 2. 再与原蒙版进行“与”运算
            # 原蒙版中，对应排除区域的部分会被强制变为 0
            mask = cv2.bitwise_and(mask, mask_exclude_inv)


        if expand_px > 0:
            # 1. 自动计算卷积核大小（例如：扩展1px -> 3x3，扩展2px -> 5x5）
            kernel_size = expand_px * 2 + 1 
            
            # 2. 生成对应大小的矩阵核
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            
            # 3. 对现有的 mask 进行膨胀（扩展）
            mask = cv2.dilate(mask, kernel, iterations=1)

        current_image = fill_watermark_with_color(current_image, mask, fill_color)
        
    print("✅ 流水线处理完成！")
    
    # 保存结果
    if not output_path:
        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_output_智能填充{ext}"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, current_image)

    end_time = time.time()
    print(f"运行耗时: {end_time - start_time:.4f} 秒")

