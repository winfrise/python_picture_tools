import cv2
import numpy as np

def sharpen_image_opencv(input_path, output_path):
    # 读取图片
    image = cv2.imread(input_path)
    
    # 定义一个 3x3 的锐化卷积核
    # 中心值为9，周围为-1，总和为1，能显著增强中心像素与周围的对比
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    
    # 应用线性滤波
    sharpened_image = cv2.filter2D(image, -1, kernel)
    
    # 保存图片
    cv2.imwrite(output_path, sharpened_image)
    print(f"OpenCV 图片已锐化并保存至: {output_path}")

# 使用示例
sharpen_image_opencv("/Users/teacher/Desktop/《临床基础检验技术》复习要点/test/page4_img1.jpeg", "/Users/teacher/Desktop/《临床基础检验技术》复习要点/test/xxx1.jpeg")