import cv2
import numpy as np

GRAY_RANGE = (160, 230)
DILATE_SIZE = 3  # 膨胀

def calculate_watermark_mask(
        img, 
        watermark_area_img, 
        gray_range = GRAY_RANGE, 
        dilate_size = DILATE_SIZE
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

    # 初始化 area_mask（默认整图都算水印区域）
    area_mask = np.ones((h, w), dtype=np.uint8) * 255

    # 处理水印区域图片
    if watermark_area_img:
        area_img = cv2.imread(watermark_area_img, cv2.IMREAD_UNCHANGED)

        if area_img & area_img.shape[-1] == 4:
            # 提取 alpha 通道
            alpha = area_img[:, :, 3]
            area_mask_raw = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)[1]
            # 缩放到输入图片尺寸
            area_mask = cv2.resize(area_mask_raw, (w, h))
            print(f"[INFO] 水印区域图片已加载，原始尺寸: {area_img.shape[:2]}, 缩放至: ({h}, {w})")

    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 灰度范围检测
    gray_range_mask = cv2.inRange(gray, gray_range[0], gray_range[1])

    # 灰度检测与区域限制的交集
    combined = cv2.bitwise_and(gray_range_mask, area_mask)

    # 膨胀
    kernel = np.ones((dilate_size, dilate_size), np.uint8)
    final_mask = cv2.dilate(combined, kernel, iterations=1)

    return final_mask
