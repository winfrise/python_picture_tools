# 获取周围像素


def get_surround_pixels(mask, y, x, radius = 5):
    """
    辅助函数：获取指定坐标周围的有效背景像素
    返回: 周围非水印区域的像素数组 (N, 3)
    """
    h, w = mask.shape
    y1 = max(0, y - radius)
    y2 = min(h, y + radius + 1)
    x1 = max(0, x - radius)
    x2 = min(w, x + radius + 1)

    # 提取邻域内的掩码和图像数据（这里假设 img 在全局或通过闭包访问，或者作为参数传入）
    # 为了通用性，这里只返回掩码切片，具体像素值在主函数获取更高效
    return mask[y1:y2, x1:x2]



