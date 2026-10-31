# draw_text_on_image.py
"""
在已有图片上绘制文字：
- 复用公共分段/高度归一化逻辑
- 位置由 offset_left（文字左边缘距图片左侧）和 offset_bottom（文字底部距图片底部）控制
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


def draw_text_on_image(
    image_path,
    text,
    output_dir=None,
    config=None,
):
    """
    在已有图片上绘制文字，返回输出路径。

    文字位置由 offset_left 和 offset_bottom 控制：
        offset_left    文字块左边缘距离图片左侧的像素距离
        offset_bottom  文字块底部（可视底部）距离图片底部的像素距离

    config 支持：
        font_path        字体文件路径
        font_size        基准字号（数字高度基准）
        text_color       文字颜色，默认 "black"
        match_digit_height  是否做数字/中文高度归一化，默认 True
        offset_left      文字左边缘距图片左侧距离（像素），默认 0
        offset_bottom    文字底部距图片底部距离（像素），默认 0
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
    offset_left        = int(config.get("offset_left", 0))
    offset_bottom      = int(config.get("offset_bottom", 0))
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

    # 3. 测量文本块（可视区域尺寸）
    bw, top_min, bottom_max = measure_text_block(segments)
    bh = bottom_max - top_min
    if bw <= 0 or bh <= 0:
        raise ValueError("文字尺寸为 0，请检查文本内容")

    # 4. 计算文字块可视区域的左上角坐标 (block_x, block_y)
    #    - 左边缘：距图片左侧 offset_left
    #    - 底边缘：距图片底部 offset_bottom  →  text_bottom_y = canvas_h - offset_bottom
    #             可视顶部 block_y = text_bottom_y - bh
    block_x = offset_left
    text_bottom_y = canvas_h - offset_bottom
    block_y = text_bottom_y - bh

    # 5. 换算成 render_text_on_canvas 需要的坐标（基于 anchor="ls"）
    #    render_text_on_canvas 用 origin_y 表示 bbox 顶部基线坐标系，
    #    这里把「可视左上角」换算回去：
    #    可视顶部 block_y 对应 bbox 顶边，而 top_min 是 bbox 相对基线的上伸量（通常 <= 0）
    first_seg_text = segments[0][0] if segments else ""
    first_b = segments[0][2].getbbox(first_seg_text, anchor="ls") if first_seg_text else (0, 0, 0, 0)
    left_min = first_b[0]

    start_x = block_x - left_min
    top_y = block_y - top_min

    # 6. 文字层单独渲染（便于单独模糊，不糊底图）
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

    # 7. 文字模糊
    if blur_radius and blur_radius > 0:
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # 8. 贴回底图（对齐回原坐标）
    if blur_pad:
        text_layer = text_layer.crop((blur_pad, blur_pad, blur_pad + canvas_w, blur_pad + canvas_h))

    result = Image.alpha_composite(base, text_layer)

    # 9. 保存
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
        "text_color": "#000000",
        "match_digit_height": True,
        "offset_left": 0,
        "offset_bottom": 0,
        "blur_radius": 0.0,
    }

    draw_text_on_image(
        image_path=image_path,
        text=gen_time_text,
        output_dir=output_dir,
        config=config,
    )