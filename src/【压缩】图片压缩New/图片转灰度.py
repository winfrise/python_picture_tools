from PIL import Image
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback


def convert_to_grayscale(input_path, output_path):
    """
    将彩色图片转换为灰度图片
    :param input_path: 原始彩色图片的路径
    :param output_path: 转换后灰度图片的保存路径
    """
    if not output_path:
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_gray.{ext}"
    try:
        # 1. 打开图片
        image = Image.open(input_path)
        
        # 2. 转换为灰度模式 ('L' 代表 Luminance，即灰度)
        gray_image = image.convert('L')
        
        # 3. 保存灰度图片
        gray_image.save(output_path)
        
        print(f"✅ 转换成功！已保存至：{output_path}")
    except Exception as e:
        print(f"❌ 转换失败：{e}")



if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/百度网盘下载/未命名文件夹/贵州宝利服饰有限公司__提取的图片"
    
    if os.path.isfile(input_path):
        output_path = None
        convert_to_grayscale(
            input_path=input_path,
            output_path=output_path,
        )
    elif os.path.isdir(input_path):
        counter = [0] 
        def callback_func(input_file, output_file):
            counter[0] += 1
            print(f"正在压缩第{counter[0]}张图片")
            convert_to_grayscale(
                input_path=input_file,
                output_path=output_file,
            )

        input_dir = input_path
        output_dir = f"{input_dir}_灰度"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else: 
         print(f"地址无效: {input_path}")