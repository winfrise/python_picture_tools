import cv2
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers.color_to_gray import color_to_gray


def calc_watermark_mask(
        img, 
        gray_range, 
        watermark_area_img=None, 
):
    """
    计算水印区域掩码（final_mask）。

    参数:
        img: 原始 BGR 图片 (numpy array)
        watermark_area_img: 水印区域图片路径，为 None 时整图作为水印区域
        gray_range: 灰度范围 (min, max)，用于阈值检测
        dilate_size: 膨胀核大小

    返回:
        final_mask: 二值掩码图片 (uint8, 255 表示水印区域)
    """
    h, w = img.shape[:2]

    ######################
    ### 处理水印区域图片
    ######################
    # 初始化 area_mask（默认整图都算水印区域）
    watermark_img_mask = np.ones((h, w), dtype=np.uint8) * 255
    if watermark_area_img:
        area_img = cv2.imread(watermark_area_img, cv2.IMREAD_UNCHANGED)

        if area_img is not None and area_img.shape[-1] == 4:
            # 提取 alpha 通道
            alpha = area_img[:, :, 3]
            mask_area_raw = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)[1]
            # 缩放到输入图片尺寸
            watermark_img_mask = cv2.resize(mask_area_raw, (w, h))
        else:
            print(f"水印区域图片错误")
    else:
        print(f"【警告】没有配置水印区域图片")


    ######################
    ### 处理灰度区域
    ######################
    # 转灰度
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 灰度范围检测， 灰色通道
    gray_range_mask = cv2.inRange(img_gray, gray_range[0], gray_range[1])  

    # 灰度检测与区域限制的交集
    final_mask = cv2.bitwise_and(watermark_img_mask, gray_range_mask)


    return final_mask
