import os, sys

from PIL import Image
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

def compress_by_color(input_path, output_path, colors=256):
    """
    通过颜色量化压缩图片
    :param input_path: 输入图片路径
    :param output_path: 输出图片路径 (建议为 PNG)
    :param colors: 目标颜色数 (1-256)，数值越小体积越小，但可能出现色带
    """
    with Image.open(input_path) as img:
        # 1. 确保为 RGB 模式 (去除 Alpha 通道干扰)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 2. 执行颜色量化
        # method=Image.MEDIANCUT 是默认且效果最好的算法
        quantized_img = img.quantize(colors=colors, method=Image.MEDIANCUT)
        
        # 3. 保存为 PNG8 格式
        # PNG 格式对索引色支持最好，压缩效率远高于 JPEG
        quantized_img.save(output_path, format='PNG', optimize=True)
        print(f"处理完成: {input_path}")

if __name__ == "__main__":
    input_path="/Users/teacher/Desktop/百度网盘下载/未命名文件夹 2/0925绿顶青山计划书__合成的图片_DPI_300_output_转DPI_output_850xauto" 
    output_path=""
    colors = 128
    if os.path.isfile(input_path):
        # 使用示例：将图片压缩至 128 色
        compress_by_color(
            input_path = input_path, 
            output_path = output_path,
            colors=colors
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            compress_by_color(
                input_path = input_file, 
                output_path = output_file,
                colors=colors
            )
        input_dir = input_path
        output_dir = f"{input_dir}_output_压缩"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )

