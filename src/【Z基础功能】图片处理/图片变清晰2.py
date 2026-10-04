import cv2
import os
import numpy as np

def enhance_scans(input_path, output_dir="enhanced_output"):
    """
    极简版：扫描件变清晰（修复文字加深逻辑）
    :param input_path: 单张图片路径 或 包含图片的文件夹路径
    :param output_dir: 输出目录
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    
    # 统一处理文件列表
    if os.path.isfile(input_path):
        files = [os.path.basename(input_path)]
        input_dir = os.path.dirname(input_path)
    elif os.path.isdir(input_path):
        input_dir = input_path
        files = [f for f in os.listdir(input_path) if f.lower().endswith(valid_extensions)]
    else:
        print("输入路径无效，请检查文件或目录是否存在。")
        return

    if not files:
        print("未找到支持的图片文件。")
        return

    for i, filename in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 处理中: {filename}")
        image_path = os.path.join(input_dir, filename)
        
        try:
            # 1. 读取并转灰度
            image = cv2.imread(image_path)
            if image is None: continue
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 2. 核心：自适应阈值二值化（去阴影、提取清晰文字）
            # 此时：文字是黑色(0)，背景是白色(255)
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 15, 10
            )
            
            # 3. 形态学闭运算：加粗文字笔画，让字迹更饱满
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 4. 【修复】全局阈值强制纯黑：确保文字绝对黑
            # 逻辑：找出所有灰度值小于 180 的像素（即文字部分），将其强制设为纯黑(0)
            # 背景保持 255（纯白）不变
            binary[binary < 180] = 0
            
            # 5. 保存结果
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_enhanced{ext}")
            cv2.imwrite(output_path, binary)
            print(f"  -> 已保存: {output_path}")
            
        except Exception as e:
            print(f"  [错误] 处理 {filename} 时发生异常: {e}")

# 直接调用方法
if __name__ == "__main__":
    # 传入图片路径 -> 单张处理
    # enhance_scans("test_doc.jpg")

    # 传入文件夹路径 -> 批量处理
    input_path = "/Users/teacher/Desktop/pdf_command/python_picture_tools/enhanced_output/未命名文件夹"
    enhance_scans(input_path)