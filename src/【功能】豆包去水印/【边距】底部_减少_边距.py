import os, sys
from PIL import Image
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

def crop_by_margins(input_path, output_path = None):
    """
    核心功能：根据四周边缘的裁剪厚度来裁剪单张图片（保持不变）
    """
    try:
        original_img = Image.open(input_path)
        original_width, original_height = original_img.size

        if not output_path:
            base_name, ext = os.path.splitext(input_path)

            output_path_min = f"{base_name}_output_min{ext}"
            output_path_max = f"{base_name}_output_max{ext}"
        else:
            output_path_min = output_path

        if output_path_min:
            # 小图片
            new_height_min = math.ceil(original_height / 1.2)
            bbox_min = (0, 0, original_width, new_height_min)
            # 执行裁剪并保存
            cropped_img_min = original_img.crop(bbox_min)
            cropped_img_min.save(output_path_min)

        if output_path_max:
            # 大图片
            new_height_max = math.floor(original_height / 1.2)
            bbox_max = (0, 0, original_width, new_height_max)
            # 执行裁剪并保存
            cropped_img_max = original_img.crop(bbox_max)
            cropped_img_max.save(output_path_max)

        print(f"✅ 成功裁剪: {os.path.basename(input_path)}")

    except Exception as e:
        print(f"❌ 处理失败 {os.path.basename(input_path)}: {e}")



# --- 测试调用示例 ---
if __name__ == "__main__":
    input_path="/Users/teacher/Desktop/未命名文件夹/02.png"

    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        crop_by_margins(
            input_path = input_path,
            output_path = None
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            crop_by_margins(
                input_path = input_file,
                output_path = output_file
            )

        input_dir = input_path
        output_dir = f"{input_path}_output_bottom"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效: {input_path}")
