
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

from tools.image_resize import resize_image

if __name__ == "__main__":

    def target_size_func (img_width, img_height):
        is_horizontal = img_width > img_height # 横向图片
        is_vertical = img_width < img_height  # 纵向图片
        if is_horizontal:
            return ['width', 100]
        return ['height', 100]

    INPUT_PATH = "/Users/teacher/Downloads/001_output_jpg"
    TARGET_SIZE = ['width', 1200] # ['height', 300]或['width', 200] 
    # TARGET_SIZE = target_size_func


    if os.path.isfile(INPUT_PATH):
        input_path = INPUT_PATH

        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_{TARGET_SIZE[0]}{TARGET_SIZE[1]}{ext}"
        resize_image(
            input_path=INPUT_PATH,
            output_path = output_path,
            target_size = TARGET_SIZE,
        )
    elif os.path.isdir(INPUT_PATH):
        def callback_func(input_file, output_file):
            resize_image(
                input_path=input_file,
                output_path= output_file,
                target_size = TARGET_SIZE,
            )
        input_dir = INPUT_PATH
        output_dir = f"{input_dir}_output_{TARGET_SIZE[0]}{TARGET_SIZE[1]}"
        batch_process_file_with_callback(
            input_dir=INPUT_PATH,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else: 
         print(f"地址无效: {INPUT_PATH}")