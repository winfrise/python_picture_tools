import os, sys
from PIL import Image
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

def convert_image(input_file, output_file = None, target_format = 'jpeg', quality = 100):

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

    # 判断格式是否支持
    supported_formats = {'jpeg', 'jpg', 'png', 'webp', 'bmp', 'gif'}
    if target_format.lower() not in supported_formats:
        print(f"不支持的格式：{target_format}，仅支持 {supported_formats}")
        return False

    print(f"正在打开文件: {input_file} -> {output_file}")

    # 开始格式转换
    try:
        # 打开图片并转换
        with Image.open(input_file) as img:
            # 如果是转换为 JPEG，且原图带有透明通道 (RGBA)，需要先转为 RGB
            no_alpha_formats = ['jpeg', 'jpg', 'bmp'] 
            if target_format.lower() in no_alpha_formats and img.mode in ('RGBA', 'P', 'LA'):
                # 注意：直接 convert('RGB') 会让透明变黑。
                # 如果希望透明变白，建议用之前的“粘贴到白底”逻辑，或者简单处理：
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3]) 
                    img = background
                else:
                    img = img.convert('RGB')
            
            img.save(
                output_file, 
                format=target_format, 
                quality=quality, 
                exif=b'', # 清除元数据
            )
            print(f"🎉 🎉 🎉 🎉 处理完成！🎉 🎉 🎉 ")
    except Exception as e:
        print(f"失败: {input_file}->{output_file}, 错误: {e}")

    
    
if __name__ == "__main__":
    # 设置你的输入和输出文件夹路径
    INPUT_PATH = "/Users/teacher/Desktop/百度网盘下载/未命名文件夹 2/000"       # 原图所在的文件夹
    TARGET_FORMAT = 'png'
    QUALITY = 100
    
    if os.path.isfile(INPUT_PATH):
        convert_image(
            input_file = INPUT_PATH,
            output_file = None,
            target_format = TARGET_FORMAT,
            quality = QUALITY,
        )
    elif os.path.isdir(INPUT_PATH):
        def callback_func(input_file, output_file):
            # 因为转文件格式，所以要修改后缀
            basename, ext = os.path.splitext(output_file)
            new_output_file = f"{basename}.{TARGET_FORMAT}"

            convert_image(
                input_file=input_file,
                output_file= new_output_file,
                target_format= TARGET_FORMAT,
                quality = QUALITY
            )

        input_dir = INPUT_PATH
        output_dir = f"{input_dir}_output_{TARGET_FORMAT}"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func = callback_func,
        )
    else:
        print(f"地址无效: {INPUT_PATH}")