import os
import numpy as np
from PIL import Image
from utils import batch_process_file_with_callback

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
            output_path = f"{base_name}_output_去水印{ext}"

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

# --- 使用示例 ---
if __name__ == "__main__":
    # 你可以传入一个图片的路径，也可以传入一个文件夹的路径
    input_path = "/Volumes/西数4T外置/Pdf修改资料/2026年8月/完成/试卷去水印ing/2026胡源 高二数学精讲精练·配套习题(1)__合成的图片"  # 例如: "photo.jpg" 或 "./my_photos/"
    input_black = 0
    input_white =  color_to_gray_level(241, 243, 242)

    if os.path.isfile(input_path):
        ps_levels_watermark_removal(
            input_path = input_path,
            input_black=input_black,
            input_white=input_white, 
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            ps_levels_watermark_removal(
                input_path = input_file,
                output_path = output_file,
                input_black=input_black,
                input_white=input_white, 
            )

        output_dir = f'{input_path}_output_去水印'
        batch_process_file_with_callback(
            input_dir=input_path,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效")