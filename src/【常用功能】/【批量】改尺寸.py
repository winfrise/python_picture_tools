from PIL import Image
import os, sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import batch_process_file_with_callback

def get_target_size(img_width, img_height):
    """
    图片大小函数：直接返回最终固定的目标尺寸
    """
    is_landscape = img_width >= img_height

    if is_landscape:
        target_width = 1430
        target_height = 1280
    else:
        target_width = 1279
        target_height = 2155

    return {
        'is_landscape': is_landscape,
        'target_width': target_width,
        'target_height': target_height,
    }


def resize_image(input_path, output_path, size_func=get_target_size):
    """
    主函数：改变图片尺寸
    """
    img = Image.open(input_path)
    orig_w, orig_h = img.size

    size_info = size_func(orig_w, orig_h)
    target_w = size_info['target_width']
    target_h = size_info['target_height']

    # 1. 判断原图是否符合目标尺寸
    already_standard = (orig_w == target_w) and (orig_h == target_h)

    # 2. 不符合则等比缩放（按 target 算比例，保证缩放后能完全覆盖目标框）
    if not already_standard:
        ratio_w = target_w / orig_w
        # ratio_h = target_h / orig_h
        scale = ratio_w

        scaled_w = round(orig_w * scale)
        scaled_h = round(orig_h * scale)

        img = img.resize((scaled_w, scaled_h), Image.LANCZOS)

    # 3. 以 target 尺寸为标准框：裁剪 / 填充
    cur_w, cur_h = img.size
    
    if cur_w > target_w or cur_h > target_h:
        # 超出 → 从底部裁剪（水平居中，垂直保留顶部）
        left = (cur_w - target_w) // 2
        top = 0 
        right = left + target_w
        bottom = top + target_h
        if left < 0:
            right = target_w
            left = 0
        img = img.crop((left, top, right, bottom))
        
    elif cur_w < target_w or cur_h < target_h:
        # 不足 → 从底部填充（水平居中、垂直贴顶部，底部留白）
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
            canvas = Image.new('RGBA', (target_w, target_h), (255, 255, 255, 255))
        else:
            canvas = Image.new('RGB', (target_w, target_h), (255, 255, 255))
            
        paste_x = (target_w - cur_w) // 2
        paste_y = 0
        mask = img if img.mode == 'RGBA' else None
        canvas.paste(img, (paste_x, paste_y), mask)
        img = canvas

    # 4. 保存
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    img.save(output_path, quality=100, subsampling=0)
    
    # 打印日志（这里打印实际缩放后的尺寸，方便你核对）
    print(f"完成: {output_path} | 原 {orig_w}x{orig_h} "
          f"-> 最终 {img.size[0]}x{img.size[1]}")
    return img.size


if __name__ == '__main__':
    input_path = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/001_横版_竖版_分类/竖版图片"

    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output{ext}"
        resize_image(input_path=input_path, output_path=output_path, size_func=get_target_size)

    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            resize_image(input_path=input_file, output_path=output_file, size_func=get_target_size)
            
        input_dir = input_path
        output_dir = f"{input_dir}_output_改尺寸"
        batch_process_file_with_callback(input_dir=input_dir, output_dir=output_dir, callback_func=callback_func)
    else:
        print(f"【错误】：输入路径既不是文件也不是目录 -> {input_path}")