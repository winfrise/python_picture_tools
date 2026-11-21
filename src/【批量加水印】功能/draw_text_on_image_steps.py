# draw_text_on_image_steps.py
"""
两步式图片文字水印：

  阶段一 generate_text_image()
      text → 渲染成一张透明底文字图 → 保存到临时文件夹（text.png）
      同时保存 meta.json 记录文字图尺寸等信息

  阶段二 compose_text_image()
      读取临时文字图 → 按 offset_left/offset_bottom 贴到 image_path → 保存结果

设计目标：临时文件夹里就是「文字图片」，可直接打开检查文字渲染是否正确；
第二步只负责「把文字图贴到指定位置」，定位问题一目了然。
"""
import os
import json
import shutil
import uuid

from PIL import Image, ImageDraw, ImageFilter

from scope_utils.text_equal_height_render_utils import (
    build_segment_fonts,
    render_text_on_canvas,
    measure_text_block,
    resolve_font_path,
    load_base_font,
    safe_filename,
)


# ============================================================
# 阶段一：text → 文字图片（一张），存临时文件夹
# ============================================================

def generate_text_image(text, config, work_dir):
    """
    把文本渲染成一张透明底文字图片，保存到 work_dir/text.png。

    返回 dict：
        {
            "text_image": ".../text.png",
            "width":  bw,   # 文字图宽（可视宽）
            "height": bh,   # 文字图高（可视高）
        }

    说明：
      - 文字图只包含文字本身的可视区域（无额外留白），透明底。
      - 后续第二步直接按这张图的尺寸做定位即可。
    """
    font_path          = config.get("font_path", "arial.ttf")
    font_size          = config.get("font_size", 40)
    text_color         = config.get("text_color", "black")
    match_digit_height = config.get("match_digit_height", True)

    os.makedirs(work_dir, exist_ok=True)

    # 1. 构建分段字体（高度归一化）
    resolved_font_path = resolve_font_path(font_path)
    if match_digit_height:
        segments, base_font, target_h = build_segment_fonts(text, resolved_font_path, font_size)
    else:
        base_font = load_base_font(resolved_font_path, font_size)
        segments = [(text, "other", base_font)]
        target_h = 0

    # 2. 测量整块可视尺寸
    bw, top_min, bottom_max = measure_text_block(segments)
    bh = bottom_max - top_min
    if bw <= 0 or bh <= 0:
        raise ValueError("文字尺寸为 0，请检查文本内容")

    # 3. 创建文字图画布（透明底，尺寸 = 可视块尺寸）
    text_img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_img)

    # 4. 计算渲染原点（anchor="ls" 基线左端）
    #    目标：让整块可视区域的左上角 = 画布 (0, 0)
    #    render_text_on_canvas 的 origin_x/origin_y 是「基线左端」在画布上的坐标。
    #    整块可视顶 = top_min（相对基线，通常 <= 0），可视左 = 首段 bbox 左边。
    #    这里沿用原逻辑：用首段 bbox 校正。
    first_seg_text = segments[0][0] if segments else ""
    first_b = segments[0][2].getbbox(first_seg_text, anchor="ls") if first_seg_text else (0, 0, 0, 0)

    # 可视左上角 → 基线左端的反算：
    #   start_x = 0 - first_b[0]
    #   top_y   = 0 - first_b[3]   （first_b[3] 是 bbox 底，相对基线；top_min 是 bbox 顶）
    # 注意：原代码用 top_y = block_y - first_b[3]，block_y=0 时即 -first_b[3]。
    start_x = -first_b[0]
    top_y   = -first_b[3]

    render_text_on_canvas(
        text_img, draw,
        start_x, top_y,
        segments, text_color, target_h,
    )

    # 5. 保存文字图
    text_image_path = os.path.join(work_dir, "text.png")
    text_img.save(text_image_path)

    # 6. 保存 meta.json（记录尺寸，便于排查）
    meta = {
        "text_image": text_image_path,
        "width": bw,
        "height": bh,
        "block_top": top_min,
        "block_bottom": bottom_max,
        "target_h": target_h,
        "text": text,
    }
    with open(os.path.join(work_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[1/2] 文字图已生成: {text_image_path}  ({bw}x{bh})")
    return meta


# ============================================================
# 阶段二：把文字图片贴到 image_path 指定位置
# ============================================================

def compose_text_image(image_path, meta, config, output_dir=None):
    """
    读取阶段一生成的文字图，按 offset_left/offset_bottom 贴到底图。

    返回输出路径。
    """
    text_image_path = meta["text_image"]
    bw = meta["width"]
    bh = meta["height"]

    offset_left   = int(config.get("offset_left", 0))
    offset_bottom = int(config.get("offset_bottom", 0))
    blur_radius   = config.get("blur_radius", 0)

    # 1. 打开底图和文字图
    base = Image.open(image_path).convert("RGBA")
    canvas_w, canvas_h = base.size

    text_layer = Image.open(text_image_path).convert("RGBA")

    # 2. 计算文字图左上角坐标
    #    - 左边缘距图左 offset_left
    #    - 底边缘距图底 offset_bottom
    block_x = offset_left
    block_y = canvas_h - offset_bottom - bh

    # 越界警告（不阻止）
    if block_x < 0 or block_y < 0 or block_x + bw > canvas_w or block_y + bh > canvas_h:
        print(f"[warn] 文字可能超出画布: pos=({block_x},{block_y}) size=({bw}x{bh}) canvas=({canvas_w}x{canvas_h})")

    # 3. 模糊（只糊文字层）
    if blur_radius and blur_radius > 0:
        pad = int(blur_radius * 6) + 2
        padded = Image.new("RGBA", (bw + 2 * pad, bh + 2 * pad), (0, 0, 0, 0))
        padded.alpha_composite(text_layer, (pad, pad))
        padded = padded.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        text_layer = padded.crop((pad, pad, pad + bw, pad + bh))

    # 4. 贴回底图
    result = base.copy()
    result.alpha_composite(text_layer, (block_x, block_y))

    # 5. 保存
    output_path = config.get("output_path", None)
    overwrite   = config.get("overwrite", True)

    if output_path is None:
        base_name, ext = os.path.splitext(os.path.basename(image_path))
        ext = ext or ".png"
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(image_path))
        os.makedirs(output_dir, exist_ok=True)
        safe_text = safe_filename(meta.get("text", ""))[:20]
        output_path = os.path.join(output_dir, f"{base_name}_{safe_text}{ext}")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if os.path.exists(output_path) and not overwrite:
            raise FileExistsError(f"输出文件已存在: {output_path}")

    save_ext = os.path.splitext(output_path)[1].lower()
    if save_ext in (".jpg", ".jpeg"):
        result.convert("RGB").save(output_path, quality=95)
    else:
        result.save(output_path)

    print(f"[2/2] 图片已生成: {output_path}")
    return output_path


# ============================================================
# 主流程
# ============================================================

def draw_text_on_image(
    image_path,
    text,
    output_dir=None,
    config=None,
    work_root=None,       # 临时文件夹根目录，默认 ./watermarks
    keep_work_dir=True,   # 是否保留临时文件夹（调试建议 True）
):
    if config is None:
        config = {}
    if callable(text):
        text = text()
    if not isinstance(text, str):
        text = str(text)

    # 建本次任务的临时目录
    if work_root is None:
        work_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watermarks")
    task_id  = uuid.uuid4().hex[:8]
    work_dir = os.path.join(work_root, task_id)

    try:
        # ---------- 阶段一：生成文字图片 ----------
        meta = generate_text_image(text, config, work_dir)

        # ---------- 阶段二：贴到 image_path ----------
        output_path = compose_text_image(image_path, meta, config, output_dir=output_dir)

        return output_path

    finally:
        if not keep_work_dir:
            try:
                shutil.rmtree(work_dir)
            except Exception:
                pass
        else:
            print(f"[keep] 临时文件夹保留: {work_dir}")


# ============================================================
# 示例
# ============================================================

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

    image_path = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/test/001/微信图片_20261028132018_1801_1.jpg"
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
        keep_work_dir=True,
    )
