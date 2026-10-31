import os
import re
import uuid
from PIL import Image, ImageDraw

from plugins.get_font_path import get_font_path
from tools.generate_random_time_str import generate_random_time_str
from scope_utils.text_render_utils import (
    _resolve_text, _load_font, _parse_color, _measure_text,
    _stretch_image, _blur_image,
)


def generate_text_image(text, output_dir="./output", config=None):
    """
    生成文字透明 PNG，效果与「直接绘制到图片」完全一致。
    """
    if config is None:
        config = {}

    font_path    = config.get("font_path", "arial.ttf")
    font_size    = config.get("font_size", 40)
    padding      = config.get("padding", 20)
    text_color   = config.get("text_color", "black")
    opacity      = config.get("opacity", None)   # 新增：统一由 _parse_color 处理
    width_ratio  = config.get("width_ratio", 1.0)
    height_ratio = config.get("height_ratio", 1.0)
    blur_radius  = config.get("blur_radius", 0)

    text = _resolve_text(text)

    # ---------- 1. 加载字体 ----------
    font = _load_font(font_path, font_size)

    # ---------- 2. 颜色解析（统一走 _parse_color） ----------
    fill_color = _parse_color(text_color, opacity)

    # ---------- 3. 测量 bbox ----------
    bbox, bw, bh = _measure_text(text, font)
    if bbox is None:
        raise ValueError("文字尺寸为 0,请检查文本内容")

    # ---------- 4. 为 blur 预留 padding ----------
    # 高斯模糊半径 r 需要 ≥ 4r 的透明余量，否则边界 alpha 会被截断削细
    blur_pad = int(max(0, blur_radius) * 6) + 2
    pad_total = padding + blur_pad

    canvas_w = bw + 2 * pad_total
    canvas_h = bh + 2 * pad_total

    # ---------- 5. 在足够大的画布上渲染文字 ----------
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    ImageDraw.Draw(canvas).text(
        (pad_total - bbox[0], pad_total - bbox[1]),
        text, font=font, fill=fill_color
    )

    # ---------- 6. 大画布 blur（边界不截断） ----------
    canvas = _blur_image(canvas, blur_radius)

    # ---------- 7. 整张画布拉伸（与旧版行为一致） ----------
    canvas = _stretch_image(canvas, width_ratio, height_ratio)

    # ---------- 8. 保存 ----------
    safe_text = re.sub(r'[\\/*?:"<>|]', "", text).strip() or uuid.uuid4().hex[:8]
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{safe_text}.png")
    canvas.save(save_path)
    print(f"图片已生成: {save_path}  "
          f"(字形 {bw}x{bh}, 画布 {canvas.size[0]}x{canvas.size[1]}, blur={blur_radius})")
    return save_path


if __name__ == "__main__":
    def gen_time_text():
        return generate_random_time_str(
            start_date_str="2026-08-12",
            end_date_str="2026-08-25",
            start_hour=9,
            end_hour=17
        )

    text = gen_time_text
    output_dir = "/Volumes/西数4T外置/百度网盘默认下载/test/文字图片"

    config = {
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "padding": 30,
        "text_color": "#000000",
        "opacity": None,          # 保持不透明；如需半透明可填 0.8 / 200
        "width_ratio": 1.0,
        "height_ratio": 1.1,
        "blur_radius": 0.7,
    }

    count = 10
    for i in range(count):
        print(f"\n--- 正在执行第 {i+1}/{count} 次 ---")
        generate_text_image(text=text, output_dir=output_dir, config=config)
    print("\n✅ 所有任务执行完成！")