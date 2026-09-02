import cv2
import numpy as np
import os


def remove_gray_watermark(
    image_path,
    output_path=None,
    roi=None,
    gray_range=(130, 220),
    inpaint_radius=5,
    debug=False,
    lower_val=160,
    upper_val=230,
    watermark_area_img=None,
):
    """
    单函数实现灰度水印去除。

    参数
    ----
    image_path : str
        输入图片路径。
    output_path : str, optional
        输出图片路径（不含后缀的文件名）。如果不传，默认保存在输入图片同级目录。
    roi : tuple, optional
        (x, y, w, h) 水印大致区域，为 None 则处理全图。
    gray_range : tuple
        水印灰度范围 (min, max)，默认 (130, 220)。
    inpaint_radius : int
        修复半径，默认 5。
    debug : bool
        是否保存中间掩码图片，默认 False。
    watermark_area_img : str, optional
        水印区域图片路径（透明PNG），非透明区域即为水印所在区域。
        在该区域内检测水印并填充白色。如果不传，按原始逻辑处理。

    返回
    ----
    tuple (result_inpaint, result_white, mask)
        result_inpaint : 智能修复结果
        result_white   : 白色填充结果
        mask           : 水印掩码
    """
    # ---- 1. 读取图片 ----
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("无法读取图片，请检查路径")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    # ---- 3. 构建掩码 ----
    mask = np.zeros((h, w), np.uint8)

    if watermark_area_img is not None:
        # ---- 使用水印区域图片作为区域限制 ----
        area_img = cv2.imread(watermark_area_img, cv2.IMREAD_UNCHANGED)
        if area_img is not None and area_img.shape[-1] == 4:
            # 有 alpha 通道，提取 alpha 作为区域掩码
            alpha = area_img[:, :, 3]
            # 二值化：alpha > 0 的区域视为水印区域
            area_mask = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)[1]
        else:
            # 没有 alpha 通道，整图作为区域
            area_mask = np.ones((h, w), np.uint8) * 255

        # 如果同时指定了 roi，进一步限制区域
        if roi:
            x, y, rw, rh = roi
            x = max(0, x)
            y = max(0, y)
            rw = min(rw, w - x)
            rh = min(rh, h - y)
            # 在 roi 范围内应用灰度检测
            region_gray = gray[y:y + rh, x:x + rw]
            region_mask = cv2.inRange(region_gray, gray_range[0], gray_range[1])
            roi_area_mask = area_mask[y:y + rh, x:x + rw]
            # 取交集：灰度检测 & 区域限制
            combined_region = cv2.bitwise_and(region_mask, roi_area_mask)
            mask[y:y + rh, x:x + rw] = combined_region
        else:
            # 全图范围，灰度检测与区域掩码取交集
            gray_range_mask = cv2.inRange(gray, gray_range[0], gray_range[1])
            combined = cv2.bitwise_and(gray_range_mask, area_mask)
            mask[:] = combined
    else:
        # ---- 原始逻辑：无水印区域图片时按灰度范围处理 ----
        if roi:
            x, y, rw, rh = roi
            x = max(0, x)
            y = max(0, y)
            rw = min(rw, w - x)
            rh = min(rh, h - y)
            region_gray = gray[y:y + rh, x:x + rw]
            region_mask = cv2.inRange(region_gray, gray_range[0], gray_range[1])
            mask[y:y + region_mask.shape[0], x:x + region_mask.shape[1]] = region_mask
        else:
            region_mask = cv2.inRange(gray, gray_range[0], gray_range[1])
            mask[:] = region_mask

    # 形态学膨胀，覆盖水印边缘
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)

    # 生成仅包含该灰度区间的掩码
    # cv2.inRange 会自动处理多通道，只要像素的 B/G/R 都在范围内即为白色(255)
    range_mask = cv2.inRange(img, (lower_val, lower_val, lower_val), (upper_val, upper_val, upper_val))

    # 【关键步骤】取交集：确保只处理原本就被识别为水印的区域
    # 防止把原本不是水印、但刚好在这个亮度区间的背景也涂白了
    final_mask = cv2.bitwise_and(mask, range_mask)

    # 执行白色填充
    result_white = img.copy()
    result_white[final_mask > 0] = [255, 255, 255]

    # ---- 7. 保存结果 ----
    cv2.imwrite(output_path, result_white)
    print(f"去水印完成，结果已保存：")
    print(f"  2. 白色填充: {output_path}")

    return result_white, mask


# ---- 使用示例 ----
if __name__ == "__main__":
    input_img_path = "/Users/teacher/Desktop/20260830/0902钢板去水印/test/test2.jpg"

    base_name, ext = os.path.splitext(input_img_path)
    output_path = f"{base_name}_output_智能填充{ext}"

    # 设定你想要填充的灰度区间 (例如：160 到 230)
    lower_val = 160 
    upper_val = 230

    watermark_area_img = "/Users/teacher/Desktop/20260830/0902钢板去水印/test/test2.jpg"

    # 示例1：不传 watermark_area_img，使用原始逻辑
    # remove_gray_watermark(
    #     image_path=input_img_path,
    #     output_path=output_path,
    #     roi=None,
    #     gray_range=(130, 220),
    #     inpaint_radius=5,
    #     debug=True,
    #     lower_val=lower_val,
    #     upper_val=upper_val,
    # )

    # 示例2：传入水印区域图片（透明PNG），非透明区域即为水印所在区域
    remove_gray_watermark(
        image_path=input_img_path,
        output_path=output_path,
        roi=None,
        gray_range=(130, 220),
        inpaint_radius=5,
        debug=True,
        lower_val=lower_val,
        upper_val=upper_val,
        watermark_area_img=watermark_area_img,  # 透明PNG
    )