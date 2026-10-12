from PIL import Image
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

def ps_levels_white_point(input_path, output_path, white_point=114):
    # 保留彩色：转成 RGB（而不是灰度 L）
    img = Image.open(input_path).convert("RGB")

    lut = []
    for i in range(256):
        if i >= white_point:
            lut.append(255)
        else:
            val = int((i / float(white_point)) * 255)
            lut.append(min(val, 255))

    # RGB 有 3 个通道，需要把同一张 256 长的表复制成 768 长
    # 若想对不同通道用不同阈值，可分别构造 R/G/B 三段表拼接
    lut_rgb = lut * 3
    new_img = img.point(lut_rgb)
    new_img.save(output_path)
    print(f"处理完成！白场阈值设为: {white_point}")



if __name__ == "__main__":
    # 你可以传入一个图片的路径，也可以传入一个文件夹的路径
    input_path = "/Users/teacher/Desktop/百度网盘下载/9-12月雅思口语题库完整版/图片"
    white_point = 200

    if os.path.isfile(input_path):
        base_name, ext = os.path.split
        output_path = f"{base_name}_output_滑块{ext}"
        ps_levels_white_point(
            input_path = input_path, 
            output_path = output_path, 
            white_point = white_point
        )

    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            ps_levels_white_point(
                input_path = input_file, 
                output_path = output_file, 
                white_point = white_point
            )

        output_dir = f'{input_path}_output_滑块去水印'
        batch_process_file_with_callback(
            input_dir=input_path,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效")