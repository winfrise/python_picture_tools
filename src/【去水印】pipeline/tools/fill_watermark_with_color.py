
import numpy as np

FILL_COLOR = [255, 255, 255]
FILL_COLOR = [0, 255, 0]
FILL_COLOR = [0, 0, 0]

def fill_watermark_with_color(img, mask, fill_color = [255, 255, 255]):
    if img is None or mask is None:
        raise ValueError("输入参数 img 和 mask 均不能为 None")


    if fill_color is None or fill_color == '':
        print("⚠️ 警告：未检测到填充颜色")
        raise

    img = img.copy()
    
    # 获取所有需要填充的水印像素坐标
    ys, xs = np.where(mask > 0)
    
    for y, x in zip(ys, xs):
        img[y, x] = fill_color
    
    return img