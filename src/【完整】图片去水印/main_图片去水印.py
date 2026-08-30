import sys
import os

# 获取当前文件(main)所在的目录: .../src/图片去水印
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取上一级目录: .../src
parent_dir = os.path.dirname(current_dir)

# 把上一级目录加入到系统搜索路径中
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


from find_exclusion_mask import find_exclusion_mask
from remove_watermark import remove_watermark
from utils import batch_process_file_with_callback

# ================= 运行测试 =================
if __name__ == "__main__":
    image_path = "/Users/teacher/Desktop/test/《四川省建设工程工程量清单计价定额——房屋建筑更新改造工程》(1)__提取的图片"
    watermark_path = "/Users/teacher/Desktop/test/mask.png"

    if os.path.isfile(image_path):
        remove_watermark(
            image_path=image_path, 
            watermark_path=watermark_path, 
            exclusion_func=find_exclusion_mask,
        )
    elif os.path.isdir(image_path):
        def callback_func (input_file, output_file):
            remove_watermark(
                image_path= input_file,
                output_path= output_file,
                watermark_path=watermark_path, 
                exclusion_func=find_exclusion_mask,
            )
        batch_process_file_with_callback(
            input_dir=image_path,
            output_dir = None,
            callback_func= callback_func
        )
    else:
        print("❌ 路径无效")