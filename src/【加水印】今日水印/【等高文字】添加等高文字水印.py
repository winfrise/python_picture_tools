# draw_text_on_image.py
"""
在已有图片上绘制文字：
- 复用公共分段/高度归一化逻辑
- 支持指定位置（左上角坐标 / 居中 / 九宫格锚点）
- 不改变底图尺寸，直接叠加
"""
import os

from PIL import Image, ImageDraw, ImageFilter

from scope_utils.text_equal_height_render_utils import (
    build_segment_fonts,
    render_text_on_canvas,
    measure_text_block,
    resolve_font_path,
    load_base_font,
    safe_filename,
)


# 九宫格锚点 -> (水平对齐, 垂直对齐)
_ANCHOR_MAP = {
    "top-left":      ("left",   "top"),
    "top-center":    ("center", "top"),
    "top-right":     ("right",  "top"),
    "middle-left":   ("left",   "middle"),
    "center":        ("center", "middle"),
    "middle-right":  ("right",  "middle"),
    "bottom-left":   ("left",   "bottom"),
    "bottom-center": ("center", "bottom"),
    "bottom-right":  ("right",  "bottom"),
}


def _calc_start_pos(anchor, canvas_w, canvas_h, bw, bh, top_min, left_min, margin, offset):
    """
    根据锚点计算文字块的起始绘制坐标 (start_x, top_y)。
    - top_y 是给 render_text_on_canvas 用的“顶部对齐线”
    - start_x 是给第一段用的起点
    """
    if anchor not in _ANCHOR_MAP:
        raise ValueError(f"未知的锚点: {anchor}，可选: {list(_ANCHOR_MAP.keys())}")

    h_align, v_align = _ANCHOR_MAP[anchor]

    # 水平
    if h_align == "left":
        block_x = margin
    elif h_align == "center":
        block_x = (canvas_w - bw) // 2
    else:  # right
        block_x = canvas_w - bw - margin

    # 垂直（block_y 是文字块可视区域的顶部）
    if v_align == "top":
        block_y = margin
    elif v_align == "middle":
        block_y = (canvas_h - bh) // 2
    else:  # bottom
        block_y = canvas_h - bh - margin

    # 转成 render_text_on_canvas 需要的形式：
    # 可视顶部 block_y 对应的是 bbox 的 bottom_max 以上的位置，
    # 而 origin_y 对应的是 bbox 的 top_min。
    top_y = block_y - top_min
    start_x = block_x - left_min

    # 额外偏移
    start_x += offset[0]
    top_y += offset[1]
    return start_x, top_y


def draw_text_on_image(
    image_path,
    text,
    output_dir=None,
    config=None,
):
    """
    在已有图片上绘制文字，返回输出路径。

    config 支持：
        font_path        字体文件路径
        font_size        基准字号（数字高度基准）
        text_color       文字颜色，默认 "black"
        match_digit_height  是否做数字/中文高度归一化，默认 True
        anchor           九宫格锚点，默认 "center"
        margin           边距（像素），默认 0
        offset           (dx, dy) 额外偏移，默认 (0, 0)
        blur_radius      文字模糊半径（只模糊文字层，不糊底图），默认 0
        output_path      指定输出路径；不指定则自动生成
        overwrite        输出文件已存在时是否覆盖，默认 True
    """
    if config is None:
        config = {}

    font_path          = config.get("font_path", "arial.ttf")
    font_size          = config.get("font_size", 40)
    text_color         = config.get("text_color", "black")
    match_digit_height = config.get("match_digit_height", True)
    anchor             = config.get("anchor", "center")
    margin             = int(config.get("margin", 0))
    offset             = config.get("offset", (0, 0))
    blur_radius        = config.get("blur_radius", 0)
    output_path        = config.get("output_path", None)
    overwrite          = config.get("overwrite", True)

    if callable(text):
        text = text()
    if not isinstance(text, str):
        text = str(text)

    # 1. 打开底图（保留 RGBA 以支持透明底图）
    base = Image.open(image_path).convert("RGBA")
    canvas_w, canvas_h = base.size

    # 2. 构建字体（复用公共逻辑）
    resolved_font_path = resolve_font_path(font_path)

    if match_digit_height:
        segments, base_font, target_h = build_segment_fonts(text, resolved_font_path, font_size)
    else:
        base_font = load_base_font(resolved_font_path, font_size)
        segments = [(text, 'other', base_font)]
        target_h = 0

    # 3. 测量文本块
    bw, top_min, bottom_max = measure_text_block(segments)
    bh = bottom_max - top_min
    if bw <= 0 or bh <= 0:
        raise ValueError("文字尺寸为 0，请检查文本内容")

    # 4. 计算绘制起点
    first_seg_text = segments[0][0] if segments else ""
    first_b = segments[0][2].getbbox(first_seg_text, anchor="ls") if first_seg_text else (0, 0, 0, 0)
    left_min = first_b[0]

    start_x, top_y = _calc_start_pos(
        anchor, canvas_w, canvas_h, bw, bh, top_min, left_min, margin, offset
    )

    # 5. 文字层单独渲染（便于单独模糊，不糊底图）
    if blur_radius and blur_radius > 0:
        blur_pad = int(blur_radius * 6) + 2
    else:
        blur_pad = 0

    text_layer = Image.new(
        "RGBA",
        (canvas_w + 2 * blur_pad, canvas_h + 2 * blur_pad),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(text_layer)

    # 因为 text_layer 有 blur_pad 的额外边距，坐标整体偏移 blur_pad
    render_text_on_canvas(
        text_layer, draw,
        start_x + blur_pad,
        top_y + blur_pad,
        segments, text_color, target_h,
    )

    # 6. 文字模糊
    if blur_radius and blur_radius > 0:
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # 7. 贴回底图（对齐回原坐标）
    if blur_pad:
        text_layer = text_layer.crop((blur_pad, blur_pad, blur_pad + canvas_w, blur_pad + canvas_h))

    result = Image.alpha_composite(base, text_layer)

    # 8. 保存
    if output_path is None:
        base_name, ext = os.path.splitext(os.path.basename(image_path))
        ext = ext or ".png"
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(image_path))
        os.makedirs(output_dir, exist_ok=True)
        safe_text = safe_filename(text)[:20]
        output_path = os.path.join(output_dir, f"{base_name}_{safe_text}{ext}")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if os.path.exists(output_path) and not overwrite:
            raise FileExistsError(f"输出文件已存在: {output_path}")

    # 根据扩展名决定保存格式
    save_ext = os.path.splitext(output_path)[1].lower()
    if save_ext in (".jpg", ".jpeg"):
        result = result.convert("RGB")
        result.save(output_path, quality=95)
    else:
        result.save(output_path)

    print(f"图片已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    from plugins.get_font_path import get_font_path
    from tools.generate_random_time_str import generate_random_time_str

    def gen_time_text():
        return generate_random_time_str(
            start_date_str="2026-08-12",
            end_date_str="2026-08-25",
            start_hour=9,
            end_hour=17,
        )

    image_path = "/Volumes/西数4T外置/百度网盘默认下载/test/11.jpg"
    output_dir = "/Volumes/西数4T外置/百度网盘默认下载/test"

    config = {
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "text_color": "#FF0000",
        "match_digit_height": True,
        "anchor": "bottom-right",
        "margin": 40,
        "offset": (0, 0),
        "blur_radius": 0.0,
    }

    draw_text_on_image(
        image_path=image_path,
        text=gen_time_text,
        output_dir=output_dir,
        config=config,
    )