import cv2
import numpy as np
import os

def replace_non_black_to_white(image_path, output_path, black_threshold=30):
    """
    将图片上所有非黑色的颜色替换为白色，保留指定区间内的黑色。
    
    :param image_path: 输入图片路径
    :param output_path: 输出图片路径
    :param black_threshold: 黑色判定阈值 (0-255)。
                            当像素的 B, G, R 三个通道的值都 <= 该阈值时，视为黑色。
    """
    # 1. 检查输入文件是否存在
    if not os.path.exists(image_path):
        print(f"错误：找不到文件 {image_path}")
        return

    # 2. 读取图片 (OpenCV 默认读取为 BGR 格式)
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图片，可能是格式不支持或文件损坏: {image_path}")
    
    # 3. 定义黑色的区间
    # lower_black: 区间下界 (纯黑)
    # upper_black: 区间上界 (深灰/阈值)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([black_threshold, black_threshold, black_threshold])
    
    # 4. 创建掩码 (Mask)
    # cv2.inRange 会返回一个单通道图像：
    # - 在 [lower, upper] 范围内的像素值为 255 (白色，代表保留)
    # - 范围外的像素值为 0 (黑色，代表需要被替换)
    mask = cv2.inRange(img, lower_black, upper_black)
    
    # 5. 【核心修复】使用 NumPy 索引直接替换颜色
    # 这一步避免了 OpenCV 矩阵运算时的维度不匹配问题
    result = img.copy()
    
    # 将 mask 中值为 0 (即非黑色区域) 的所有像素点，赋值为白色 [255, 255, 255]
    # NumPy 会自动处理多通道赋值，无需手动转换维度
    result[mask == 0] = [255, 255, 255]
    
    # 6. 保存结果
    # 确保输出目录存在（如果 output_path 包含子目录）
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    success = cv2.imwrite(output_path, result)
    
    if success:
        print(f"✅ 处理成功！结果已保存至: {output_path}")
        print(f"   原图尺寸: {img.shape}, 黑色阈值设定为: {black_threshold}")
    else:
        print("❌ 保存图片失败，请检查输出路径权限。")

# --- 主程序入口 ---
if __name__ == "__main__":
    # 配置参数
    INPUT_IMAGE = "/Users/teacher/Downloads/中小学教师业务考试资料333__提取的图片/page1_img1_IM8.png"       # 请修改为你的实际图片文件名
    base_name, ext = os.path.splitext(INPUT_IMAGE) # 处理后的图片文件名
    OUTPUT_IMAGE = f"{base_name}_output{ext}"
    THRESHOLD = 180                 # 黑色阈值：0-255。数值越大，保留的深色越多
    
    # 执行处理
    try:
        replace_non_black_to_white(
            image_path=INPUT_IMAGE, 
            output_path=OUTPUT_IMAGE, 
            black_threshold=THRESHOLD
        )
    except Exception as e:
        print(f"发生异常: {e}")
