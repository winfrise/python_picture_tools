import os, sys
from PIL import Image
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback


def resize_image(input_file, output_file, target_size):

    target_attr = target_size[0]
    target_val = target_size[1]

    # 1. 打开图片
    img = Image.open(input_file)
    orig_width, orig_height = img.size

    if target_attr.lower() == 'width':
        new_width = int(target_val)
        new_height = round(orig_height / orig_width * new_width)
    elif target_attr.lower() == 'height':
        new_height = int(target_val)
        new_width = round(orig_width / orig_height * new_height)
    else:
        print(f'参数无法识别: {target_attr}')

    # 改变图片大小
    new_img = img.resize((new_width, new_height), Image.LANCZOS)

    # 4. 确保输出目录存在并保存图片
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)

    new_img.save(output_file)
    print(f"处理完成！已保存至: {output_file}")

if __name__ == "__main__":

    INPUT_PATH = "/Users/teacher/Desktop/百度网盘下载/0925去水印/1转图片"

     # TARGET_SIZE = ['width', 200]
    TARGET_SIZE = ['height', 300]

    target_attr = TARGET_SIZE[0]
    target_val = TARGET_SIZE[1]
    if os.path.isfile(INPUT_PATH):
        input_file = INPUT_PATH

        base_name, ext = os.path.splitext(input_file)
        output_file = f"{base_name}_output_{target_attr}{target_val}{ext}"
        resize_image(
            input_file=INPUT_PATH,
            output_file = output_file,
            target_size = TARGET_SIZE,
        )
    elif os.path.isdir(INPUT_PATH):
        def callback_func(input_file, output_file):
            resize_image(
                input_file=input_file,
                output_file= output_file,
                target_size = TARGET_SIZE,
            )
        input_dir = INPUT_PATH
        output_dir = f"{input_dir}_output_{target_attr}{target_val}"
        batch_process_file_with_callback(
            input_dir=INPUT_PATH,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else: 
         print(f"地址无效: {INPUT_PATH}")
