import cv2
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers.color_to_gray import color_to_gray


def get_watermark_img_mask(
        img, 
        mask, 
        watermark_area_img, 
):
    img_h, img_w = img.shape[:2]
    if mask is None:
        mask = np.ones((img_h, img_w), dtype=np.uint8) * 255

    area_img = cv2.imread(watermark_area_img, cv2.IMREAD_UNCHANGED)

    if area_img is not None and area_img.shape[-1] == 4:
        # 提取 alpha 通道
        alpha = area_img[:, :, 3]
        mask_area_raw = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)[1]
        # 缩放到输入图片尺寸
        watermark_img_mask = cv2.resize(mask_area_raw, (img_w, img_h))
        mask = cv2.bitwise_and(mask, watermark_img_mask)
    else:
        print(f"水印区域图片错误")


    return mask
