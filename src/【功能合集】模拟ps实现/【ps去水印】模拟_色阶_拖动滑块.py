from PIL import Image
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

def ps_levels_white_point(input_path, output_path, white_point=114):
    """
    模拟 PS 色阶：调整白场（右侧滑块）
    :param white_point: 对应 PS 中输入色阶的右侧数值 (0-255)
    """
    img = Image.open(input_path).convert("L") # 转为灰度图处理
    
    # 构建查找表 (LUT)
    # 逻辑：如果像素值 >= white_point，直接变 255 (纯白)
    # 否则：将其拉伸。例如 white_point=114，则 114->255, 57->127...
    lut = []
    for i in range(256):
        if i >= white_point:
            lut.append(255)
        else:
            # 线性拉伸公式：(当前值 / 白场值) * 255
            val = int((i / float(white_point)) * 255)
            lut.append(min(val, 255))
            
    # 应用变换
    new_img = img.point(lut)
    new_img.save(output_path)
    print(f"处理完成！白场阈值设为: {white_point}")




if __name__ == "__main__":
    # 你可以传入一个图片的路径，也可以传入一个文件夹的路径
    input_path = "/Users/teacher/Desktop/百度网盘下载/公式大全/公式大全__合成的图片_DPI_300"
    white_point = 216

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