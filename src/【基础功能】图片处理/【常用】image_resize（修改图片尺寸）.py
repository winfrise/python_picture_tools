import os
from PIL import Image
from utils import batch_process_file_with_callback

INPUT_PATH = "/Users/teacher/Downloads/百度网盘Download/新建文件夹 (2)-4/未命名文件夹 2"
OUTPUT_PATH = "/Users/teacher/Downloads/百度网盘Download/新建文件夹 (2)-4/未命名文件夹2222"
WIDTH = 2400 # 数值(px) / auto
HEIGHT = 1800 # 数值(px) / auto
MODE = "crop" # crop / fill

def resize_image(input_file, output_file, width, height, mode = "fill"):
    # 1. 打开图片
    img = Image.open(input_file)
    orig_width, orig_height = img.size

    # 2. 处理宽高参数（将 'auto' 或字符串数字转换为整数）
    is_width_auto = str(width).lower() == 'auto'
    is_height_auto = str(height).lower() == 'auto'


    # --- 情况 A：包含 auto，保持原图比例缩放 ---
    if is_width_auto or is_height_auto:
        if is_width_auto and is_height_auto:
            new_width, new_height = orig_width, orig_height
        elif is_width_auto:
            new_height = int(height)
            ratio = new_height / orig_height
            new_width = round(orig_width * ratio)
        else:  # height is auto
            new_width = int(width)
            ratio = new_width / orig_width
            new_height = round(orig_height * ratio)

        # Auto 模式下直接调整大小
        img = img.resize((new_width, new_height), Image.LANCZOS)

    # --- 情况 B：宽高都有具体数值 ---
    else:
        target_w = int(width)
        target_h = int(height)

        if mode == 'stretch':
            # 强制拉伸
            img = img.resize((target_w, target_h), Image.LANCZOS)

        elif mode == 'fill':
            # 留白填充 (Letterbox)
            # 计算缩放比例，取较小值以保证图片能完全放入
            ratio = min(target_w / orig_width, target_h / orig_height)
            new_w = round(orig_width * ratio)
            new_h = round(orig_height * ratio)

            # 先缩放
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)

            # 创建白色背景画布
            img = Image.new('RGB', (target_w, target_h), (255, 255, 255))
            # 居中粘贴
            paste_x = (target_w - new_w) // 2
            paste_y = (target_h - new_h) // 2
            img.paste(img_resized, (paste_x, paste_y))

        else:
            # 居中裁剪 (Center Crop) - 默认模式
            # 计算缩放比例，取较大值以保证填满画布
            ratio = max(target_w / orig_width, target_h / orig_height)
            new_w = round(orig_width * ratio)
            new_h = round(orig_height * ratio)

            # 先放大/缩小到刚好覆盖目标尺寸
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)

            # 计算裁剪区域
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            right = left + target_w
            bottom = top + target_h

            # 裁剪
            img = img_resized.crop((left, top, right, bottom))


    # 4. 确保输出目录存在并保存图片
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    if output_file.lower().endswith(('.jpg', '.jpeg')) and img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    img.save(output_file)
    print(f"处理完成！已保存至: {output_file}")

if __name__ == "__main__":
    
    if os.path.isfile(INPUT_PATH):
        resize_image(
            input_file=INPUT_PATH,
            output_file = OUTPUT_PATH,
            width = WIDTH,
            height = HEIGHT,
            mode = MODE,
        )
    elif os.path.isdir(INPUT_PATH):
        def callback_func(input_file, output_file):
            resize_image(
                input_file=input_file,
                output_file= output_file,
                width = WIDTH,
                height = HEIGHT,
                mode = MODE
            )
        batch_process_file_with_callback(
            input_dir=INPUT_PATH,
            output_dir=OUTPUT_PATH,
            callback_func=callback_func,
        )
