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

    # ---- 2. 解析路径信息 ----
    base_dir = os.path.dirname(image_path)
    file_name = os.path.splitext(os.path.basename(image_path))[0]
    file_ext = os.path.splitext(image_path)[1]

    # 生成默认输出路径
    if output_path:
        base, ext = os.path.splitext(output_path)
        path_inpaint = f"{base}_inpaint{ext}"
        path_white = f"{base}_white_fill{ext}"
        # 确保输出目录存在
        dir_name = os.path.dirname(output_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
    else:
        path_inpaint = os.path.join(base_dir, f"{file_name}_output_inpaint{file_ext}")
        path_white = os.path.join(base_dir, f"{file_name}_output_white_fill{file_ext}")

    # ---- 3. 构建掩码 ----
    mask = np.zeros((h, w), np.uint8)

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

    # ---- 4. Debug 模式：保存掩码 ----
    if debug:
        debug_mask_path = os.path.join(base_dir, f"{file_name}_debug_mask{file_ext}")
        cv2.imwrite(debug_mask_path, mask)
        print(f"[Debug] 已保存掩码图片至: {debug_mask_path}")

    # ---- 5. 智能修复 (Inpainting) ----
    result_inpaint = cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)

    # ---- 6. 白色填充 ----
    result_white = img.copy()
    result_white[mask > 0] = [255, 255, 255]

    # ---- 7. 保存结果 ----
    cv2.imwrite(path_inpaint, result_inpaint)
    cv2.imwrite(path_white, result_white)
    print(f"去水印完成，结果已保存：")
    print(f"  1. 智能修复: {path_inpaint}")
    print(f"  2. 白色填充: {path_white}")

    return result_inpaint, result_white, mask


# ---- 使用示例 ----
if __name__ == "__main__":
    input_img_path = "/Users/teacher/Desktop/20260830/0902钢板去水印/test/组合 1_页面_183.jpg"
    output_path = "/Users/teacher/Desktop/20260830/0902钢板去水印/test/组合 1_页面_183xxx.jpg"

    result_inpaint, result_white, mask = remove_gray_watermark(
        image_path=input_img_path,
        output_path=output_path,
        roi=None,
        gray_range=(130, 220),
        inpaint_radius=5,
        debug=True,
    )