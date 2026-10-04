import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm

# 1. 您提供的基础纠偏函数（保持不变）
def deskew_by_edge(image_path):
    image = cv2.imread(str(image_path)) # 兼容 Path 对象
    if image is None:
        return None, "无法读取图像"
        
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=50, maxLineGap=10)
    
    if lines is None or len(lines) == 0:
        return image, "未检测到有效边缘，保持原样"
        
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) < 45: 
            angles.append(angle)
            
    if not angles:
        return image, "未检测到水平线，保持原样"
        
    median_angle = np.median(angles)
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    corrected = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return corrected, f"成功纠偏: {median_angle:.2f}°"

# 2. 新增：批量处理函数
def batch_deskew(input_dir, output_dir, supported_ext=('.jpg', '.jpeg', '.png', '.bmp')):
    """
    批量读取文件夹中的图片，进行纠偏后保存到输出文件夹。
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 自动创建输出文件夹
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 获取所有支持格式的图片
    image_files = [f for f in input_path.iterdir() if f.suffix.lower() in supported_ext]
    
    if not image_files:
        print(f"⚠️ 在 {input_dir} 中没有找到支持的图片文件。")
        return

    print(f"🚀 开始批量处理，共 {len(image_files)} 个文件...")
    
    # 使用 tqdm 显示进度条
    for img_file in tqdm(image_files, desc="纠偏进度"):
        try:
            corrected_img, msg = deskew_by_edge(img_file)
            
            if corrected_img is not None:
                # 拼接输出路径并保存
                save_path = output_path / f"fixed_{img_file.name}"
                cv2.imwrite(str(save_path), corrected_img)
                tqdm.write(f"✅ [{img_file.name}] {msg}")
            else:
                tqdm.write(f"❌ [{img_file.name}] 处理失败: {msg}")
                
        except Exception as e:
            tqdm.write(f"❌ [{img_file.name}] 发生异常: {str(e)}")

# 3. 运行示例
if __name__ == "__main__":
    input_dir = "/Users/teacher/Desktop/完成/去水印/11__提取的图片"
    output_dir = "/Users/teacher/Desktop/完成/去水印/11__提取的图片2"
    batch_deskew(
        input_dir=input_dir,     
        output_dir=output_dir 
    )