import cv2
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def detect_shape_mask(
        img,
        detect_shape_img,
        threshold=0.8,
        scale_range=None,
):
    """
    通过模板匹配检测图像中指定形状的位置，返回形状二值掩码。

    参数:
        img: 原始 BGR 图片 (numpy array)
        detect_shape_img: 形状模板图片路径（透明PNG），背景透明的形状图片
        threshold: 模板匹配置信度阈值 (0~1)，越高要求越严格
        scale_range: 多尺度匹配范围 (min_scale, max_scale, step)，
                     用于形状在目标图中尺寸不一致的场景。
                     例如 (0.5, 1.5, 0.1) 表示从 0.5x 到 1.5x 以 0.1 为步长尝试缩放。
                     为 None 时不进行缩放匹配（使用原始尺寸）。

    返回:
        shape_mask: 二值掩码 (uint8)，255 表示检测到的形状区域，0 表示背景
        match_info: dict 包含匹配位置、置信度、缩放比例等信息，检测失败时返回 None
    """
    h, w = img.shape[:2]
    shape_mask = np.zeros((h, w), dtype=np.uint8)

    shape_img = cv2.imread(detect_shape_img, cv2.IMREAD_UNCHANGED)
    if shape_img is None:
        print(f"【错误】无法读取形状模板图片: {detect_shape_img}")
        return shape_mask, None

    if shape_img.shape[-1] != 4:
        print(f"【错误】形状模板图片必须为透明PNG（含alpha通道），当前通道数: {shape_img.shape[-1]}")
        return shape_mask, None

    # 提取 alpha 通道获取形状二值图
    alpha = shape_img[:, :, 3]
    _, shape_binary = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)

    # 获取形状轮廓及边界框
    contours, _ = cv2.findContours(shape_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"【错误】形状模板中未检测到有效轮廓")
        return shape_mask, None

    all_points = np.vstack(contours)
    x, y, tw, th = cv2.boundingRect(all_points)

    # 提取形状区域的 BGR 图（用于模板匹配的纹理信息）
    shape_bgr = cv2.cvtColor(shape_img, cv2.COLOR_BGRA2BGR)
    template = shape_bgr[y:y + th, x:x + tw]
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # 记录原始轮廓点（用于后续在结果图上精确绘制形状）
    original_contours = contours
    original_offset = (x, y)

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 确定匹配尺度列表
    scales = [1.0]
    if scale_range is not None:
        min_s, max_s, step = scale_range
        scales = np.arange(min_s, max_s + step * 0.5, step).tolist()
        # 确保 1.0 在列表中
        if 1.0 not in scales:
            scales.append(1.0)
            scales.sort()

    best_score = 0.0
    best_loc = None
    best_scale = 1.0

    for scale in scales:
        if scale == 1.0:
            scaled_template = template_gray
        else:
            new_w = int(template_gray.shape[1] * scale)
            new_h = int(template_gray.shape[0] * scale)
            if new_w < 5 or new_h < 5:
                continue
            scaled_template = cv2.resize(template_gray, (new_w, new_h))

        # 模板匹配
        result = cv2.matchTemplate(img_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_score:
            best_score = max_val
            best_loc = (max_loc[0], max_loc[1])
            best_scale = scale

    # 判断是否达到阈值
    if best_score >= threshold and best_loc is not None:
        match_x, match_y = best_loc
        match_tw = int(tw * best_scale)
        match_th = int(th * best_scale)

        # 创建形状掩码
        shape_mask = np.zeros((h, w), dtype=np.uint8)

        if scale_range and best_scale != 1.0:
            # 缩放匹配：用矩形近似覆盖匹配区域
            cv2.rectangle(shape_mask,
                          (match_x, match_y),
                          (match_x + match_tw, match_y + match_th),
                          255, -1)
        else:
            # 原始尺寸：用精确轮廓绘制
            scale_factor = best_scale
            scaled_contours = []
            for cnt in original_contours:
                scaled_cnt = (cnt * scale_factor).astype(np.int32)
                shifted_cnt = scaled_cnt + np.array([[match_x + original_offset[0],
                                                       match_y + original_offset[1]]])
                scaled_contours.append(shifted_cnt)
            cv2.drawContours(shape_mask, scaled_contours, -1, 255, -1)

        match_info = {
            "found": True,
            "position": (match_x, match_y),
            "size": (match_tw, match_th),
            "confidence": float(best_score),
            "scale": float(best_scale),
        }
        print(f"【形状检测】匹配成功 | 位置=({match_x}, {match_y}) | "
              f"大小={match_tw}x{match_th} | 置信度={best_score:.4f} | "
              f"缩放={best_scale:.2f}x")
    else:
        match_info = {
            "found": False,
            "position": None,
            "size": None,
            "confidence": float(best_score),
            "scale": float(best_scale),
        }
        print(f"【形状检测】未匹配到形状（最高置信度={best_score:.4f}，阈值={threshold}）")

    return shape_mask
