import cv2
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers.color_to_gray import color_to_gray


def get_gray_mask(
        img,
        mask, 
        gray_range, 
):
    img_h, img_w = img.shape[:2]
    if mask is None:
        mask = np.ones((img_h, img_w), dtype=np.uint8) * 255

    masked_img = cv2.bitwise_and(img, img, mask=mask)

    # 转灰度
    img_gray = cv2.cvtColor(masked_img, cv2.COLOR_BGR2GRAY)
    # 灰度范围检测， 灰色通道
    gray_range_mask = cv2.inRange(img_gray, gray_range[0], gray_range[1])  

    return gray_range_mask
