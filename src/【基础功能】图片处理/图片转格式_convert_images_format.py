import os
from PIL import Image
from utils import batch_process_file_with_callback

def convert_image(input_file, output_file = None, target_format = 'jpeg', quality = 90):

    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件 '{input_file}' 不存在！")
        return False
    
    if not target_format:
        print(f"处理文件失败:【{input_file}】目标格式不能为空")    
        return

    if not output_file:
        base_name, ext = os.path.splitext(input_file)
        new_ext = f".{target_format}"
        output_file = f"{base_name}_output{new_ext}"
    
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)


    print(f"正在打开文件: {input_file} -> {output_file}")

    # 修改后缀名
    # new_ext = '.jpg' if target_format == 'JPEG' else f'.{target_format.lower()}'
    # new_path = os.path.join(new_dir, base_name + new_ext)

    try:
        # 打开图片并转换
        with Image.open(input_file) as img:
            # 如果是转换为 JPEG，且原图带有透明通道 (RGBA)，需要先转为 RGB
            if target_format.lower() == 'jpeg' and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            img.save(output_file, format=target_format, quality=quality)
            print(f"🎉 🎉 🎉 🎉 处理完成！🎉 🎉 🎉 ")
    except Exception as e:
        print(f"失败: {input_file}->{output_file}, 错误: {e}")

    
    
if __name__ == "__main__":
    # 设置你的输入和输出文件夹路径
    INPUT_PATH = "/Users/teacher/Downloads/百度网盘下载/施工图片/施工图片修改"       # 原图所在的文件夹
    OUTPUT_PATH = "/Users/teacher/Downloads/百度网盘下载/施工图片/施工图片修改111" # 转换后保存的文件夹
    TARGET_FORMAT = 'jpeg'
    QUALITY = 100
    
    if os.path.isfile(INPUT_PATH):
        convert_image(
            input_file = INPUT_PATH,
            output_file = None,
            target_format = TARGET_FORMAT
        )
    elif os.path.isdir(INPUT_PATH):
        def callback_func(input_file, output_file, target_format, quality):

            basename, ext = os.path.splitext(output_file)
            output_file = f"{basename}.{target_format}"

            convert_image(
                input_file=input_file,
                output_file= output_file,
                target_format= target_format,
                quality = quality
            )
        batch_process_file_with_callback(
            input_dir=INPUT_PATH,
            output_dir=OUTPUT_PATH,
            target_format = TARGET_FORMAT,
            callback_func=callback_func,
            quality = QUALITY
        )