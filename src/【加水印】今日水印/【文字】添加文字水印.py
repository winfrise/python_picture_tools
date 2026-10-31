from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
import os, sys
import random
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

from tools.generate_random_time_str import generate_random_time_str

def get_font_path(font_name="苹方黑体-中粗-简.ttf"):
    """
    获取项目 assets/fonts 目录下字体的绝对路径。
    
    Args:
        font_name (str): 字体文件名，默认为 "苹方黑体-中粗-简.ttf"
        
    Returns:
        str: 字体的绝对路径字符串。如果文件不存在，返回 None 并打印警告。
    """
    # 1. 获取当前脚本所在的绝对目录
    # __file__ 指向当前代码所在的 .py 文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 向上回退一级到 src 目录，再进入 assets/fonts
    # 假设当前文件在 src/某文件夹/ 下，所以需要 ".."
    font_dir = os.path.join(current_dir, "..", "assets", "fonts")
    
    # 3. 规范化路径（消除 .. 符号）并拼接文件名
    full_path = os.path.normpath(os.path.join(font_dir, font_name))
    
    # 4. 检查文件是否存在
    if os.path.exists(full_path):
        return full_path
    else:
        print(f"⚠️ 警告：未找到字体文件 -> {full_path}")
        return None

def _parse_color(color, opacity):
    """颜色 + 透明度 -> (R, G, B, A)"""
    if isinstance(color, str):
        rgba = ImageColor.getrgb(color)
    elif isinstance(color, (tuple, list)):
        rgba = tuple(color)
    else:
        raise ValueError(f"不支持的颜色格式: {color}")

    if len(rgba) == 3:
        r, g, b = rgba
        a = 255
    else:
        r, g, b, a = rgba

    if opacity is not None:
        if isinstance(opacity, float) and 0.0 <= opacity <= 1.0:
            a = int(a * opacity)
        else:
            a = int(max(0, min(255, opacity)))
    return (r, g, b, a)


def add_texts_to_image(input_path, output_path, text, config=None):
    """
    在图片上添加多行文字，从下往上排列，支持半透明、动态文字、高斯模糊
    新增 width_ratio / height_ratio：控制文字的宽/高拉伸比例（默认 1.0 即不拉伸）
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入图片: {input_path}")

    if config is None:
        config = {}
    font_size = config.get("font_size", 100)
    color = config.get("color", "red")
    opacity = config.get("opacity", 128)
    font_path = config.get("font_path", None)
    margin_left = config.get("margin_left", 20)
    margin_bottom = config.get("margin_bottom", 20)
    blur_radius = config.get("blur_radius", 0)
    width_ratio = config.get("width_ratio", 1.0)      # 【新增】文字宽度拉伸比例
    height_ratio = config.get("height_ratio", 1.0)    # 【新增】文字高度拉伸比例

    if callable(text):
        text = text()

    # 确保最终拿到的是字符串
    if not isinstance(text, str):
        text = str(text)

    base = Image.open(input_path).convert("RGBA")
    img_width, img_height = base.size

    # 加载字体
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
            print("警告: 未找到指定字体文件，正在使用默认字体。")
    except Exception as e:
        print(f"字体加载失败: {e}，使用默认字体。")
        font = ImageFont.load_default()

    fill_color = _parse_color(color, opacity)

    # ---- 先测量文字尺寸 ----
    # 用一个临时 draw 测量（不实际绘制）
    measure_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    measure_draw = ImageDraw.Draw(measure_img)
    bbox = measure_draw.textbbox((0, 0), text, font=font)
    raw_w = bbox[2] - bbox[0]
    raw_h = bbox[3] - bbox[1]

    # 防止空文本/零尺寸
    if raw_w <= 0 or raw_h <= 0:
        print(f"警告: 文本 '{text}' 尺寸为 0，跳过绘制。")
        return

    # ---- 若有宽高比例，则把文字画到独立小图再 resize ----
    scale_w = width_ratio if width_ratio and width_ratio > 0 else 1.0
    scale_h = height_ratio if height_ratio and height_ratio > 0 else 1.0

    if abs(scale_w - 1.0) > 1e-6 or abs(scale_h - 1.0) > 1e-6:
        # 在临时图层上按原始尺寸绘制文字（留出 bbox 偏移）
        text_img = Image.new("RGBA", (raw_w, raw_h), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        # 把 bbox 左上角对齐到 (0,0)
        text_draw.text((-bbox[0], -bbox[1]), text, font=font, fill=fill_color)

        # 计算拉伸后的尺寸
        new_w = max(1, int(round(raw_w * scale_w)))
        new_h = max(1, int(round(raw_h * scale_h)))
        text_img = text_img.resize((new_w, new_h), Image.LANCZOS)

        text_w, text_h = new_w, new_h
        # 拉伸后直接粘贴到文字层，位置由 margin 决定
        # 基准位置：仍然以 margin_left / margin_bottom 作为左/下边距
        x = margin_left
        y = img_height - margin_bottom - text_h
        if y < -text_h or y > img_height:
            print(f"警告: 文本 '{text}' 的坐标 y={y} 可能在画布外！")

        text_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        text_layer.paste(text_img, (x, y), text_img)
    else:
        # 不拉伸：走原来的流程
        text_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        text_h = raw_h
        y = img_height - margin_bottom - text_h - bbox[1]
        x = margin_left
        if y < -text_h or y > img_height:
            print(f"警告: 文本 '{text}' 的坐标 y={y} 可能在画布外！")
        draw.text((x, y), text, font=font, fill=fill_color)

    # 对文字图层做高斯模糊（只模糊文字，背景不受影响）
    if blur_radius and blur_radius > 0:
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    result = Image.alpha_composite(base, text_layer)

    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg", ".bmp"):
        background = Image.new("RGB", result.size, (255, 255, 255))
        background.paste(result, mask=result.split()[3])
        background.save(output_path)
    else:
        result.save(output_path)


# ================= 动态文字函数 =================
def random_time_near(base_time_str, hours_range=2, fmt="%Y-%m-%d %H:%M:%S"):
    base = datetime.strptime(base_time_str, fmt)
    delta_seconds = int(timedelta(hours=hours_range).total_seconds())
    rand_seconds = random.randint(-delta_seconds, delta_seconds)
    return (base + timedelta(seconds=rand_seconds)).strftime(fmt)


def gen_time_text():
    random_time = generate_random_time_str(
        start_date_str="2026-05-05",
        end_date_str="2026-06-30",
        start_hour=9,
        end_hour=17
    )
    return random_time


# ================= 测试调用示例 =================
if __name__ == "__main__":
    input_path = "/Volumes/西数4T外置/百度网盘默认下载/37张图片/8月"

    text = gen_time_text

    font_path=get_font_path("苹方黑体-中黑-简.ttf")
    print(font_path)
    config = {
        "font_path": font_path,
        "font_size": 36,  # 会比ps字体小1-2个像素
        "color": "#000000",
        "opacity": 255,
        "margin_left": 256,
        "margin_bottom": 656,
        "blur_radius": 0.8,
        "width_ratio": 1.0,    # 【新增】1.0=原宽，1.2=拉宽20%，0.8=压缩到80%
        "height_ratio": 1.1,   # 【新增】1.0=原高，1.2=拉高20%，0.8=压缩到80%
    }

    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output{ext}"
        add_texts_to_image(
            input_path=input_path,
            output_path=output_path,
            text=text,
            config=config
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            add_texts_to_image(
                input_path=input_file,
                output_path=output_file,
                text=text,
                config=config
            )

        input_dir = input_path
        base_name, ext = os.path.splitext(input_path)
        output_dir = f"{base_name}_output"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"【错误】：输入路径既不是文件也不是目录 -> {input_path}")