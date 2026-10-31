import os
import re
import uuid
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from plugins.get_font_path import get_font_path
from tools.generate_random_time_str import generate_random_time_str



# ============ 新增：文本分段 + 高度归一化 ============
def split_text_by_script(text):
    """
    把文本切分成连续片段，每段标记类型：'digit' 或 'other'。
    例如 "8月12日 09:30" -> [('8','digit'), ('月','other'), ('12','digit'), ('日 09','other'), ...]
    更准确地说，按"字符是否为 ASCII 数字"聚合连续同类字符。
    """
    if not text:
        return []
    segments = []
    cur_type = 'digit' if text[0].isdigit() else 'other'
    cur_chars = [text[0]]
    for ch in text[1:]:
        t = 'digit' if ch.isdigit() else 'other'
        if t == cur_type:
            cur_chars.append(ch)
        else:
            segments.append((''.join(cur_chars), cur_type))
            cur_type = t
            cur_chars = [ch]
    segments.append((''.join(cur_chars), cur_type))
    return segments


def measure_pixel_height(text, font):
    """返回文字实际渲染的像素高度（含上下伸部）。"""
    if not text:
        return 0
    bbox = font.getbbox(text)
    return max(1, bbox[3] - bbox[1])


def build_segment_fonts(text, font_path, base_size):
    """
    为每段文字返回 (segment_text, type, font) 列表。
    - 'other' 段用 base_size。
    - 'digit' 段用 base_size 渲染后，若其像素高度低于同字号下中文的像素高度，
      则按比例放大字号，使像素高度相等。
    """
    # 先测一次同字号下"中文/other"字符的像素高度作为基准
    try:
        base_font = ImageFont.truetype(font_path, base_size) if font_path and os.path.exists(font_path) \
            else ImageFont.load_default()
    except Exception:
        base_font = ImageFont.load_default()

    # 用一个非数字、非空白的字符来估计"中文高度"；若文本里没有，就用全角字符
    sample_chars = [c for c in text if not c.isdigit() and not c.isspace()]
    sample_other = sample_chars[0] if sample_chars else "国"
    target_h = measure_pixel_height(sample_other, base_font)

    # 测一个数字字符在 base_size 下的高度
    sample_digit = next((c for c in text if c.isdigit()), "0")
    digit_h_base = measure_pixel_height(sample_digit, base_font)

    if digit_h_base <= 0 or target_h <= 0:
        return [(t, typ, base_font) for t, typ in split_text_by_script(text)]

    # 数字字号：按高度比例放大
    if digit_h_base < target_h:
        digit_size = max(1, int(round(base_size * target_h / digit_h_base)))
    else:
        digit_size = base_size  # 数字本来就更高就不缩小（避免视觉变细），按需求也可改成等比缩小

    try:
        digit_font = ImageFont.truetype(font_path, digit_size) if font_path and os.path.exists(font_path) \
            else ImageFont.load_default()
    except Exception:
        digit_font = base_font

    # 二次校正（字体量化字号后高度可能不精确，微调 1~2 号）
    for _ in range(4):
        h = measure_pixel_height(sample_digit, digit_font)
        if h == target_h:
            break
        if h < target_h:
            digit_size += 1
        else:
            digit_size -= 1
        digit_size = max(1, digit_size)
        try:
            digit_font = ImageFont.truetype(font_path, digit_size) if font_path and os.path.exists(font_path) \
                else ImageFont.load_default()
        except Exception:
            break

    result = []
    for seg_text, typ in split_text_by_script(text):
        result.append((seg_text, typ, digit_font if typ == 'digit' else base_font))
    return result, base_font


def render_text_on_canvas(canvas, draw, origin_x, origin_y, segments, fill):
    """
    逐段绘制，返回整体 bbox（相对于 canvas 坐标），便于后续裁剪/对齐。
    基线对齐：每段都用 anchor='ls'（左基线），保证数字与中文底部对齐。
    """
    x = origin_x
    y_baseline = origin_y
    for seg_text, typ, font in segments:
        draw.text((x, y_baseline), seg_text, font=font, fill=fill, anchor="ls")
        # 用该段字体测量前进宽度
        seg_bbox = font.getbbox(seg_text, anchor="ls")
        x += seg_bbox[2] - seg_bbox[0]
    return x


# ============ 原有函数改造 ============
def generate_text_image(text, output_dir="./output", config=None):
    """
    生成文字透明 PNG，效果与「直接绘制到图片」完全一致：
    - 数字与中文视觉高度对齐
    - 光栅化参数与 add_texts_to_image 相同
    - 模糊在带 padding 的画布上做（边界不被截断）
    - 拉伸在模糊之前/之后均可，但必须保持笔画粗细语义一致
    """
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
    # 新增可选：是否强制数字与中文等高（默认 True）
    match_digit_height = config.get("match_digit_height", True)

    if callable(text):
        text = text()
    if not isinstance(text, str):
        text = str(text)

    # ---------- 1. 加载字体 & 构建分段 ----------
    resolved_font_path = font_path if (font_path and os.path.exists(font_path)) else None
    if resolved_font_path is None:
        print("警告: 未找到指定字体文件，正在使用默认字体。")

    if match_digit_height:
        segments, base_font = build_segment_fonts(text, resolved_font_path, font_size)
    else:
        try:
            base_font = ImageFont.truetype(resolved_font_path, font_size) if resolved_font_path \
                else ImageFont.load_default()
        except Exception as e:
            print(f"字体加载失败: {e}，使用默认字体。")
            base_font = ImageFont.load_default()
        segments = [(text, 'other', base_font)]

    # ---------- 2. 测量整体 bbox（用统一基线 anchor='ls' 测量） ----------
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    # 计算整体宽度和最高/最低（各段字体不同，高度需分别看）
    total_w = 0
    top_min = 0
    bottom_max = 0
    for seg_text, typ, font in segments:
        if not seg_text:
            continue
        b = font.getbbox(seg_text, anchor="ls")  # 左基线
        total_w += (b[2] - b[0])
        top_min = min(top_min, b[1])
        bottom_max = max(bottom_max, b[3])

    bw = total_w
    bh = bottom_max - top_min
    if bw <= 0 or bh <= 0:
        raise ValueError("文字尺寸为 0，请检查文本内容")

    # ---------- 3. 为 blur 预留足够 padding ----------
    blur_pad = int(max(0, blur_radius) * 6) + 2
    pad_total = padding + blur_pad

    canvas_w = bw + 2 * pad_total
    canvas_h = bh + 2 * pad_total

    # ---------- 4. 在足够大的画布上渲染文字 ----------
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # 基线 y：让整体字形落在画布竖直居中的区域
    # 画布内容区从 pad_total 开始，内容高度 bh；top 对应 top_min
    baseline_y = pad_total - top_min
    # 水平起点：内容区左边界 - 第一段的左边界偏移（anchor='ls' 时 bbox[0] 通常为 0 或负）
    first_b = segments[0][2].getbbox(segments[0][0], anchor="ls") if segments[0][0] else (0, 0, 0, 0)
    start_x = pad_total - first_b[0]

    render_text_on_canvas(canvas, draw, start_x, baseline_y, segments, text_color)

    # ---------- 5. blur ----------
    if blur_radius and blur_radius > 0:
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # ---------- 6. 非等比拉伸 ----------
    if abs(width_ratio - 1.0) > 1e-6 or abs(height_ratio - 1.0) > 1e-6:
        new_w = max(1, int(round(canvas_w * width_ratio)))
        new_h = max(1, int(round(canvas_h * height_ratio)))
        canvas = canvas.resize((new_w, new_h), Image.LANCZOS)

    # ---------- 7. 保存 ----------
    safe_text = re.sub(r'[\\/*?:"<>|]', "", text).strip() or uuid.uuid4().hex[:8]
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{safe_text}.png")
    canvas.save(save_path)
    print(f"图片已生成: {save_path}  "
          f"(字形 {bw}x{bh}, 画布 {canvas.size[0]}x{canvas.size[1]}, blur={blur_radius})")
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
    output_dir = "/Volumes/西数4T外置/百度网盘默认下载/test"

    config = {
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "padding": 30,
        "text_color": "#000000",
        "bg_color": (255, 255, 255, 0),
        "width_ratio": 1.0,
        "height_ratio": 1.1,
        "blur_radius": 0.7,        # 新增：模糊半径，0 表示不模糊
    }

    count = 10

    for i in range(count):
        print(f"\n--- 正在执行第 {i+1}/{count} 次 ---")
        generate_text_image(
            text=text, 
            output_dir=output_dir, 
            config=config
        )
    print("\n✅ 所有任务执行完成！")