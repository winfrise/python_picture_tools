# generate_text_image.py
"""
生成透明背景文字图片（原逻辑保持不变，只是把公共逻辑抽到 text_render_common.py）
"""
import os
from PIL import Image, ImageDraw, ImageFilter

from plugins.get_font_path import get_font_path
from tools.generate_random_time_str import generate_random_time_str

from scope_utils.text_equal_height_render_utils import (
    build_segment_fonts,
    render_text_on_canvas,
    measure_text_block,
    resolve_font_path,
    load_base_font,
    safe_filename,
)


def generate_text_image(text, output_dir="./output", config=None):
    if config is None:
        config = {}

    font_path    = config.get("font_path", "arial.ttf")
    font_size    = config.get("font_size", 40)
    padding      = config.get("padding", 20)
    text_color   = config.get("text_color", "black")
    bg_color     = config.get("bg_color", (255, 255, 255, 0))
    width_ratio  = config.get("width_ratio", 1.0)
    height_ratio = config.get("height_ratio", 1.0)
    blur_radius  = config.get("blur_radius", 0)
    match_digit_height = config.get("match_digit_height", True)

    if callable(text):
        text = text()
    if not isinstance(text, str):
        text = str(text)

    # 1. 构建字体
    resolved_font_path = resolve_font_path(font_path)

    if match_digit_height:
        segments, base_font, target_h = build_segment_fonts(text, resolved_font_path, font_size)
    else:
        base_font = load_base_font(resolved_font_path, font_size)
        segments = [(text, 'other', base_font)]
        target_h = 0

    # 2. 测量整体 bbox
    total_w, top_min, bottom_max = measure_text_block(segments)
    bw = total_w
    bh = bottom_max - top_min
    if bw <= 0 or bh <= 0:
        raise ValueError("文字尺寸为 0，请检查文本内容")

    # 3. 画布尺寸
    blur_pad = int(max(0, blur_radius) * 6) + 2
    pad_total = padding + blur_pad
    canvas_w = bw + 2 * pad_total
    canvas_h = bh + 2 * pad_total

    # 4. 渲染
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    top_y = pad_total - top_min
    first_b = segments[0][2].getbbox(segments[0][0], anchor="ls") if segments[0][0] else (0, 0, 0, 0)
    start_x = pad_total - first_b[0]

    render_text_on_canvas(canvas, draw, start_x, top_y, segments, text_color, target_h)

    # 5. 模糊
    if blur_radius and blur_radius > 0:
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # 6. 拉伸
    if abs(width_ratio - 1.0) > 1e-6 or abs(height_ratio - 1.0) > 1e-6:
        new_w = max(1, int(round(canvas_w * width_ratio)))
        new_h = max(1, int(round(canvas_h * height_ratio)))
        canvas = canvas.resize((new_w, new_h), Image.LANCZOS)

    # 7. 保存
    safe_text = safe_filename(text)
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{safe_text}.png")
    canvas.save(save_path)

    print(f"图片已生成: {save_path}")
    return save_path


if __name__ == "__main__":
    def gen_time_text():
        random_time = generate_random_time_str(
            start_date_str="2026-08-12",
            end_date_str="2026-08-25",
            start_hour=9,
            end_hour=17
        )
        return random_time

    text = gen_time_text
    output_dir = "/Volumes/西数4T外置/百度网盘默认下载/test/等高文字"

    config = {
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "padding": 30,
        "text_color": "#000000",
        "bg_color": (255, 255, 255, 0),
        "width_ratio": 1.0,
        "height_ratio": 1.1,
        "blur_radius": 0.7,
        "match_digit_height": True,
    }

    count = 10

    for i in range(count):
        print(f"\n--- 正在执行第 {i+1}/{count} 次 ---")
        generate_text_image(text=text, output_dir=output_dir, config=config)
    print("\n✅ 所有任务执行完成！")