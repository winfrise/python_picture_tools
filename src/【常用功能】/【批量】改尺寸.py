from PIL import Image
import os, sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import batch_process_file_with_callback

def get_target_size(img_width, img_height):
    """
    图片大小函数
    根据横版/竖版返回：
      - standard_width / standard_height: 标准框尺寸（最终输出尺寸）
      - target_width  / target_height : 同比缩放后的尺寸（用于缩放原图）

    横版: 宽度缩放到 1279，标准框宽度=1279，高度=1280
    竖版: 高度缩放到 1280，标准框高度=1280，宽度=1279
    """
    is_landscape = img_width >= img_height

    if is_landscape:
        # 横版：高度缩放到 1280
        ratio_w_h = img_width / img_height

        standard_height = 1280
        standard_width = round(standard_height * ratio_w_h)

        target_height = 1280
        # target_width = round(target_height * ratio_w_h)
        target_width = 1430

    else:
        # 竖版：宽度缩放到 1279

        # 1. 先算原图的高度比 (高/宽)
        ratio_h_w = img_height / img_width

        standard_width = 1279
        standard_height = round(standard_width * ratio_h_w)

        target_width = 1279
        target_height = 2155
        # target_height = round(target_width * ratio_h_w)

    return {
        'is_landscape': is_landscape,
        'standard_width': standard_width,
        'standard_height': standard_height,
        'target_width': target_width,
        'target_height': target_height,
    }


def resize_image(input_path, output_path, size_func=get_target_size):
    """
    主函数：改变图片尺寸
    1. 调用 size_func 得到标准框尺寸和同比缩放后的尺寸
    2. 若原图尺寸不符合标准，则同比缩放到 target_width x target_height
    3. 以 standard_width x standard_height 为标准框：
       - 超出 → 从底部裁剪（保留顶部，裁掉底部超出部分）
       - 不足 → 从底部填充（内容贴顶部，底部白色填充）
    """
    img = Image.open(input_path)
    orig_w, orig_h = img.size

    size_info = size_func(orig_w, orig_h)
    is_landscape   = size_info['is_landscape']
    standard_w     = size_info['standard_width']
    standard_h     = size_info['standard_height']
    target_w       = size_info['target_width']
    target_h       = size_info['target_height']

    # 1. 判断原图是否符合标准尺寸
    already_standard = (orig_h == standard_h) and (orig_w == standard_w)

    # 2. 不符合则同比缩放
    if not already_standard:
        ratio_w = standard_w / orig_w
        ratio_h = standard_h / orig_h
        scale = max(ratio_w, ratio_h)

        # 计算缩放后的目标尺寸
        target_w_new = round(orig_w * scale)
        target_h_new = round(orig_h * scale)

        img = img.resize((target_w_new, target_h_new), Image.LANCZOS)

    # 3. 以 standard 尺寸为标准框：裁剪 / 填充
    cur_w, cur_h = img.size
    if cur_w > standard_w or cur_h > standard_h:
        # 超出 → 从底部裁剪（保留顶部，裁掉底部超出部分）
        # 水平方向超出部分居中裁剪；垂直方向保留顶部，裁掉底部
        left = (cur_w - standard_w) // 2
        top = 0  # 从顶部开始，保留顶部内容
        right = left + standard_w
        bottom = top + standard_h
        # 若水平方向未超出，left 会为负数，用 0 修正
        if left < 0:
            right = standard_w
            left = 0
        img = img.crop((left, top, right, bottom))
    elif cur_w < standard_w or cur_h < standard_h:
        # 不足 → 从底部填充（水平居中、垂直贴顶部，底部留白）
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
            canvas = Image.new('RGBA', (standard_w, standard_h), (255, 255, 255, 255))
        else:
            canvas = Image.new('RGB', (standard_w, standard_h), (255, 255, 255))
        # 水平居中，垂直贴顶部
        paste_x = (standard_w - cur_w) // 2
        paste_y = 0
        mask = img if img.mode == 'RGBA' else None
        canvas.paste(img, (paste_x, paste_y), mask)
        img = canvas

    # 4. 保存
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    img.save(output_path, quality=100, subsampling=0)
    print(f"完成: {output_path} | 原 {orig_w}x{orig_h} "
          f"-> 缩放 {target_w}x{target_h} -> 最终 {img.size[0]}x{img.size[1]}")
    return img.size


if __name__ == '__main__':
    input_path = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/001"

    # 单个文件处理
    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output{ext}"

        resize_image(
            input_path=input_path,
            output_path=output_path,
            size_func= get_target_size
        )

    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            resize_image(
                input_path=input_file,
                output_path=output_file,
                size_func= get_target_size
            )
        input_dir = input_path
        output_dir = f"{input_dir}_output_改尺寸"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func
        )
    else:
        print(f"【错误】：输入路径既不是文件也不是目录 -> {input_path}")