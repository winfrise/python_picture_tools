import cv2
import numpy as np
import os

def image_enhancement_pipeline(image_path):
    # 1. 读取图像
    img = cv2.imread(image_path)
    if img is None:
        print("错误：无法读取图像，请检查路径。")
        return
    
    # 2. 灰度化 (Grayscale)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. 高斯模糊降噪 (Gaussian Blur)
    # 核大小设为 (5, 5)，标准差设为 0（由核大小自动计算）
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 4. 去除阴影 (Shadow Removal)
    # 使用形态学“顶帽运算” (Top-Hat Transform)
    # 原理：提取图像中比周围区域更亮的细节，常用于消除不均匀的背景光照/阴影
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))
    shadow_removed = cv2.morphologyEx(blurred, cv2.MORPH_TOPHAT, kernel)
    
    # 5. 对比度调整 (Contrast Adjustment)
    # 使用 CLAHE (自适应直方图均衡化)，比全局均衡化效果更好，不会过度放大噪声
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(shadow_removed)
    
    # 6. 边缘检测 (Canny Edge Detection)
    # 阈值可根据实际图像效果微调
    edges = cv2.Canny(enhanced, threshold1=50, threshold2=150)
    
    # --- 结果展示 ---
    # --- 结果展示与保存 ---
    # 将每一步的结果和对应的文件名放入列表，方便循环处理
    results = [
        ("01_原图", img),
        ("02_灰度化", gray),
        ("03_高斯模糊", blurred),
        ("04_去阴影", shadow_removed),
        ("05_对比度增强", enhanced),
        ("06_Canny边缘检测", edges)
    ]

    # 获取原图所在的文件夹路径
    save_dir = os.path.dirname(image_path)
    # 获取原图的文件名（不含扩展名），用于命名新图片
    base_name, ext = os.path.splitext(os.path.basename(image_path))

    for step_name, image_data in results:
        # 拼接保存路径：原图目录 + 步骤名称 + 原图文件名 + .png
        save_path = os.path.join(save_dir, f"{step_name}_{base_name}.png")
        cv2.imwrite(save_path, image_data)
        print(f"✅ 已保存: {save_path}")

# 运行示例（请替换为你本地图像的路径）
if __name__ == "__main__":
    image_path = "/Users/teacher/Desktop/test/111.png"
    image_enhancement_pipeline(
        image_path = image_path
    )