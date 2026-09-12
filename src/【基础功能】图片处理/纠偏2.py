import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
import os

def deskew_by_projection(image_path, output_path=None, limit_angle=15):
    """
    基于投影法和轮廓分析的稳健纠偏算法
    :param image_path: 输入图片路径
    :param output_path: 输出图片路径（可选）
    :param limit_angle: 最大允许纠偏角度，超过此角度可能视为拍摄错误而非倾斜
    """
    # 1. 读取图像
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"[Error] 无法读取图像: {image_path}")
        return False

    # 2. 预处理：灰度化 + 二值化 (OTSU自动阈值)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 二值化：文字变白，背景变黑
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 3. 形态学操作：连接文字笔画，形成“行”或“块”
    # 使用长条形的核进行膨胀，有助于连接同一行的文字
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 10)) 
    dilated = cv2.dilate(binary, kernel, iterations=1)

    # 4. 寻找轮廓
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        print(f"[Warn] 未检测到内容: {image_path}")
        return False

    # 5. 筛选有效轮廓并计算角度
    # 我们收集所有大面积轮廓的角度，取中位数以减少误差
    angles = []
    h, w = img.shape[:2]
    min_area = (h * w) * 0.005  # 忽略极小的噪点块

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
            
        # 获取最小外接矩形
        rect = cv2.minAreaRect(contour)
        angle = rect[2]
        
        # OpenCV的角度定义比较特殊，需要修正到 -45 ~ 45 度之间
        # 这里的逻辑是为了统一角度标准
        if angle < -45:
            angle = 90 + angle
            
        angles.append(angle)

    if not angles:
        return False

    # 6. 计算最终角度（使用中位数，抗干扰能力比平均值强）
    final_angle = np.median(angles)

    # 如果角度非常小（例如小于0.5度），则不处理，避免画质损失
    if abs(final_angle) < 0.5:
        print(f"[Skip] 角度过小 ({final_angle:.2f}°)，跳过: {os.path.basename(image_path)}")
        return True

    # 限制最大角度，防止过度旋转
    if abs(final_angle) > limit_angle:
        print(f"[Warn] 检测到角度过大 ({final_angle:.2f}°)，可能是非文档图片，跳过: {os.path.basename(image_path)}")
        return True

    # 7. 执行旋转
    # 获取旋转矩阵
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, final_angle, 1.0)
    
    # 执行仿射变换
    # borderValue=(255, 255, 255) 设置旋转后的背景填充为白色
    rotated_img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))

    # 8. 保存结果
    save_path = output_path if output_path else image_path
    cv2.imwrite(str(save_path), rotated_img)
    print(f"[Success] 纠偏 {final_angle:.2f}° -> {os.path.basename(save_path)}")
    return True


def batch_deskew(input_dir, output_dir=None, file_types=['*.jpg', '*.png', '*.bmp', '*.jpeg']):
    """
    批量处理文件夹下的图片
    """
    input_path = Path(input_dir)
    
    # 如果指定了输出目录，则创建；否则在原目录覆盖
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
    else:
        out_path = input_path

    # 收集所有文件
    files = []
    for f_type in file_types:
        files.extend(list(input_path.glob(f_type)))
    
    if not files:
        print("未找到任何图片文件！")
        return

    print(f"找到 {len(files)} 张图片，开始处理...")

    # 使用 tqdm 显示进度条
    for img_path in tqdm(files, desc="Processing"):
        # 构建输出路径
        target_path = out_path / img_path.name
        
        try:
            deskew_by_projection(img_path, target_path)
        except Exception as e:
            print(f"\n[Error] 处理失败 {img_path}: {e}")

# === 使用示例 ===
if __name__ == "__main__":
    # 设置输入文件夹路径
    input_folder = "/Users/teacher/Desktop/完成/去水印/11__提取的图片" 
    
    # 设置输出文件夹路径（如果不填，会覆盖原图，建议填一个新文件夹）
    output_folder = "/Users/teacher/Desktop/完成/去水印/11__提取的图片-22" 
    
    # 确保输入文件夹存在
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)
        print(f"已创建输入文件夹: {input_folder}，请将图片放入其中。")
    else:
        batch_deskew(input_folder, output_folder)