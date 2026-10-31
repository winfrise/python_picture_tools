from PIL import Image, ImageDraw
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback
from tools.generate_random_time_str import generate_random_time_str
from scope_utils.text_render_utils import (
    _resolve_text, _load_font, _parse_color, _measure_text,
    _stretch_image, _blur_image,
)


def get_font_path(font_name="苹方黑体-中粗-简.ttf"):
    """获取项目 assets/fonts 目录下字体的绝对路径。"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(current_dir, "..", "assets", "fonts")
    full_path = os.path.normpath(os.path.join(font_dir, font_name))
    if os.path.exists(full_path):
        return full_path
    print(f"⚠️ 警告：未找到字体文件 -> {full_path}")
    return None


def add_texts_to_image(input_path, output_path, text, config=None):
    """
    在图片上添加文字，从下往上排列，支持半透明、动态文字、高斯模糊、宽高拉伸。
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入图片: {input_path}")

    if config is None:
        config = {}

    font_size     = config.get("font_size", 100)
    color         = config.get("color", "red")
    opacity       = config.get("opacity", 128)
    font_path     = config.get("font_path", None)
    margin_left   = config.get("margin_left", 20)
    margin_bottom = config.get("margin_bottom", 20)
    blur_radius   = config.get("blur_radius", 0)
    width_ratio   = config.get("width_ratio", 1.0)
    height_ratio  = config.get("height_ratio", 1.0)

    text = _resolve_text(text)

    base = Image.open(input_path).convert("RGBA")
    img_width, img_height = base.size

    # ---------- 字体 + 颜色（统一走 _parse_color） ----------
    font = _load_font(font_path, font_size)
    fill_color = _parse_color(color, opacity)

    # ---------- 测量 ----------
    bbox, raw_w, raw_h = _measure_text(text, font)
    if bbox is None:
        print(f"警告: 文本 '{text}' 尺寸为 0，跳过绘制。")
        return

    need_scale = (
        abs(width_ratio - 1.0) > 1e-6 or abs(height_ratio - 1.0) > 1e-6
    )

    if need_scale:
        # ---- 拉伸路径：先画紧贴小图 -> 拉伸 -> 粘贴 ----
        text_img = Image.new("RGBA", (raw_w, raw_h), (0, 0, 0, 0))
        ImageDraw.Draw(text_img).text(
            (-bbox[0], -bbox[1]), text, font=font, fill=fill_color
        )
        text_img = _stretch_image(text_img, width_ratio, height_ratio)

        text_w, text_h = text_img.size
        x = margin_left
        y = img_height - margin_bottom - text_h
        if y < -text_h or y > img_height:
            print(f"警告: 文本 '{text}' 的坐标 y={y} 可能在画布外！")

        text_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        text_layer.paste(text_img, (x, y), text_img)
    else:
        # ---- 不拉伸路径：直接在大图层上绘制 ----
        text_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        y = img_height - margin_bottom - raw_h - bbox[1]
        x = margin_left
        if y < -raw_h or y > img_height:
            print(f"警告: 文本 '{text}' 的坐标 y={y} 可能在画布外！")
        ImageDraw.Draw(text_layer).text(
            (x, y), text, font=font, fill=fill_color
        )

    # ---------- 文字图层模糊 ----------
    text_layer = _blur_image(text_layer, blur_radius)

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
    return generate_random_time_str(
        start_date_str="2026-05-05",
        end_date_str="2026-06-30",
        start_hour=9,
        end_hour=17
    )


# ================= 测试调用示例 =================
if __name__ == "__main__":
    input_path = "/Volumes/西数4T外置/百度网盘默认下载/37张图片/8月"

    text = gen_time_text
    font_path = get_font_path("苹方黑体-中黑-简.ttf")
    print(font_path)

    config = {
        "font_path": font_path,
        "font_size": 36,
        "color": "#000000",
        "opacity": 255,
        "margin_left": 256,
        "margin_bottom": 656,
        "blur_radius": 0.8,
        "width_ratio": 1.0,
        "height_ratio": 1.1,
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