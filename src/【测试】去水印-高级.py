import cv2
import numpy as np

class GrayWatermarkRemover:
    def __init__(self, image_path):
        # 读取图片
        self.img = cv2.imread(image_path)
        if self.img is None:
            raise ValueError("无法读取图片，请检查路径")
        
        # 预处理：转灰度图，用于后续提取水印
        self.gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        
        # 获取图片尺寸，用于ROI区域裁剪
        self.h, self.w = self.img.shape[:2]

    def remove(self, roi=None, gray_range=(140, 230), inpaint_radius=5):
        """
        :param roi: 参数1-水印大致区域 (x, y, w, h)，如果为None则处理全图
        :param gray_range: 参数2-水印的灰度范围 (min, max)。
                           通常水印是浅灰(150-220)，正文是深黑(0-100)。
        :param inpaint_radius: 参数3-修复半径。数值越大，修补范围越大，但也越容易模糊。
        """
        # 1. 准备掩码画布（全黑）
        mask = np.zeros((self.h, self.w), np.uint8)
        
        # 确定处理区域
        if roi:
            x, y, w, h = roi
            # 边界检查
            x = max(0, x); y = max(0, y)
            w = min(w, self.w - x); h = min(h, self.h - y)
            region_gray = self.gray[y:y+h, x:x+w]
        else:
            region_gray = self.gray
            x, y = 0, 0

        # 2. 在水印区域内匹配灰度（提取浅灰色水印）
        # cv2.inRange 会把范围内的像素变白(255)，范围外的变黑(0)
        region_mask = cv2.inRange(region_gray, gray_range[0], gray_range[1])
        
        # 将局部掩码贴回全局掩码
        mask[y:y+region_mask.shape[0], x:x+region_mask.shape[1]] = region_mask

        # 可选：形态学膨胀，让掩码稍微大一点，确保覆盖水印边缘
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

        # 3. 执行修复（Inpainting）
        # cv2.INPAINT_TELEA 算法速度较快，适合文档
        result = cv2.inpaint(self.img, mask, inpaint_radius, cv2.INPAINT_TELEA)

        return result, mask

# --- 使用示例 ---
if __name__ == "__main__":
    remover = GrayWatermarkRemover('/Users/teacher/Desktop/20260830/0902钢板去水印/test/组合 1_页面_183.jpg')
    
    # 假设水印主要在中间，可以指定区域 (x,y,w,h)
    # 如果不指定区域，直接传 None，程序会自动根据灰度全图匹配
    cleaned_img, mask_img = remover.remove(
        roi=None,                # 参数1：处理全图
        gray_range=(130, 220),   # 参数2：提取灰度在130到220之间的像素（即浅灰色水印）
        inpaint_radius=5         # 参数3：修复半径
    )

    # 显示结果
    cv2.imshow("Original Mask", mask_img) # 查看提取出的水印形状
    cv2.imshow("Cleaned Result", cleaned_img)
    cv2.waitKey(0)
    cv2.imwrite("result.jpg", cleaned_img)

