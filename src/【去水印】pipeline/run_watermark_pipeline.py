import numpy as np
from typing import List, Dict, Any, Callable
import time
import cv2
import os

from tools.calc_watermark_mask import calc_watermark_mask
from tools.fill_watermark_with_color import fill_watermark_with_color
from tools.get_rgb_mask import get_rgb_mask


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
        fill_color = step.get("fill_color")
        

        mask = calc_watermark_mask(
            img = current_image, 
            watermark_area_img=watermark_area_img,
            gray_range= [
                target_gray - target_gray_threshold, 
                target_gray + target_gray_threshold
            ]
        )

        # 排除指定颜色的rgb蒙版
        if exclude_rgb_list:
            mask_exclude = get_rgb_mask(
                img = current_image, 
                color_rgb_list=exclude_rgb_list
            )
            mask = cv2.bitwise_and(mask, mask_exclude)

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

