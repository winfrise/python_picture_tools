import os
import numpy as np
from PIL import Image

def color_to_gray_level(r=None, g=None, b=None, hex_color=None):
    """
    将 RGB 或 Hex 颜色转换为 0-255 的灰度值（用于 input_black/white）
    """
    if hex_color:
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    if r is not None and g is not None and b is not None:
        # 使用标准亮度公式计算灰度
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        return int(round(gray))
    
    raise ValueError("请提供 RGB 值或 Hex 颜色代码")

def ps_levels_watermark_removal(input_path, output_path = None, input_black=0, input_white=255, gamma=1.0):
    """
    模拟 PS 色阶调整去除水印
    :param input_path: 原始图片路径
    :param output_path: 输出图片路径
    :param input_black: 黑场阈值 (0-255)，低于此值的像素将变为纯黑
    :param input_white: 白场阈值 (0-255)，高于此值的像素将变为纯白
    :param gamma: 灰度系数/伽马值，控制中间调亮度
    """
    
    try:

        if not output_path:
            base_name, ext = os.path.splitext(input_path)
            output_path = f"{base_name}_output{ext}"

        img = Image.open(input_path).convert('RGB')
        img_array = np.array(img, dtype=np.float32)
        
        if input_black >= input_white:
            print(f"[错误] {input_path} 处理失败: 黑场阈值必须小于白场阈值！")
            return
            
        clamped = np.clip(img_array, input_black, input_white)
        normalized = (clamped - input_black) / (input_white - input_black)
        corrected = np.power(normalized, 1.0 / gamma)
        result_array = np.clip(corrected * 255, 0, 255).astype(np.uint8)
        
        result_img = Image.fromarray(result_array, 'RGB')
        result_img.save(output_path)
        print(f"[成功] 已保存至: {output_path}")
    except Exception as e:
        print(f"[错误] 处理 {input_path} 时发生异常: {e}")

def batch_process(input_path, output_dir, input_black=10, input_white=220, gamma=1.0):
    """
    批量处理入口：自动判断输入是单张图片还是文件夹
    """
    # 支持的图片格式
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 判断输入路径类型
    if os.path.isfile(input_path):
        # 1. 如果输入的是单个文件
        _, ext = os.path.splitext(input_path)
        if ext.lower() in valid_extensions:
            filename = os.path.basename(input_path)
            output_path = os.path.join(output_dir, f"no_wm_{filename}")
            ps_levels_watermark_removal(input_path, output_path, input_black, input_white, gamma)
        else:
            print(f"[跳过] {input_path} 不是支持的图片格式。")
            
    elif os.path.isdir(input_path):
        # 2. 如果输入的是文件夹
        print(f"正在扫描文件夹: {input_path}")
        file_list = [f for f in os.listdir(input_path) 
                     if os.path.splitext(f)[1].lower() in valid_extensions]
        
        if not file_list:
            print("[提示] 该文件夹下没有找到支持的图片文件。")
            return
            
        for filename in file_list:
            file_path = os.path.join(input_path, filename)
            output_path = os.path.join(output_dir, f"no_wm_{filename}")
            ps_levels_watermark_removal(file_path, output_path, input_black, input_white, gamma)
            
    else:
        print(f"[错误] 路径不存在: {input_path}")

# --- 使用示例 ---
if __name__ == "__main__":
    # 你可以传入一个图片的路径，也可以传入一个文件夹的路径
    input_path = "/Volumes/西数4T外置/Pdf修改资料/2026年8月/完成/试卷去水印ing/test/page_003.jpg"  # 例如: "photo.jpg" 或 "./my_photos/"
    input_black = 0
    input_white =  color_to_gray_level(241, 243, 242)

    if os.path.isfile(input_path):
        ps_levels_watermark_removal(
            input_path = input_path,
            input_black=input_black,
            input_white=input_white, 
        )
    elif os.path.isdir(input_path):
        batch_process(
            input_path=input_path, 
            input_black=input_black, 
            input_white=input_white, 
            gamma=1.0
        )
    else:
        print(f"地址无效")