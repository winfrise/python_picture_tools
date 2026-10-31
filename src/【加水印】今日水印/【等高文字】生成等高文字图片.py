import os
import re
import uuid
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from plugins.get_font_path import get_font_path
from tools.generate_random_time_str import generate_random_time_str


# ============ 文本分段 + 高度归一化 ============
def split_text_by_script(text):
    """
    把文本切分成连续片段，每段标记类型：'digit' 或 'other'。
    按"字符是否为 ASCII 数字"聚合连续同类字符。
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
    以「数字在 base_size 下的像素高度」为基准，
    中文按比例缩放字号，使像素高度与数字一致。
    返回 (segments, base_font, target_h)
    """
    def load_font(size):
        try:
            if font_path and os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except Exception:
            pass
        return ImageFont.load_default()

    base_font = load_font(base_size)

    # 找数字基准
    sample_digit = next((c for c in text if c.isdigit()), None)
    if sample_digit is None:
        return [(text, 'other', base_font)], base_font, 0

    target_h = measure_pixel_height(sample_digit, base_font)

    # 找中文样本
    sample_chars = [c for c in text if not c.isascii() and not c.isspace()]
    if not sample_chars:
        return [(t, typ, base_font) for t, typ in split_text_by_script(text)], base_font, target_h

    sample_cn = sample_chars[0]
    cn_h_base = measure_pixel_height(sample_cn, base_font)

    if target_h <= 0 or cn_h_base <= 0:
        return [(t, typ, base_font) for t, typ in split_text_by_script(text)], base_font, target_h

    # 按高度比例缩放中文字号
    cn_size = max(1, int(round(base_size * target_h / cn_h_base)))
    cn_font = load_font(cn_size)

    # 二次微调
    for _ in range(4):
        h = measure_pixel_height(sample_cn, cn_font)
        if h == target_h:
            break
        cn_size += 1 if h < target_h else -1
        cn_size = max(1, cn_size)
        cn_font = load_font(cn_size)

    # 组装 segments
    result = []
    for seg_text, _ in split_text_by_script(text):
        typ = 'digit' if seg_text and seg_text[0].isdigit() else 'other'
        result.append((seg_text, typ, base_font if typ == 'digit' else cn_font))
    
    return result, base_font, target_h


def render_text_on_canvas(canvas, draw, origin_x, origin_y, segments, fill, target_h):
    """
    逐段绘制。
    origin_y 为整体文本的“顶部对齐线”。
    数字正常绘制，中文根据实际高度计算垂直偏移 dy，使其与数字在垂直方向完全居中对齐。
    """
    x = origin_x
    for seg_text, typ, font in segments:
        if not seg_text:
            continue
        
        # 获取当前段在当前字体下的 bbox
        bbox = font.getbbox(seg_text, anchor="ls")
        
        # 如果设定了目标高度(即数字的高度)，计算当前段的垂直偏移
        dy = 0
        if target_h > 0:
            seg_h = bbox[3] - bbox[1]
            # 核心逻辑：中文向下偏一点，让它与数字的中心线对齐
            dy = (target_h - seg_h) / 2.0
            
            # 对于数字本身，不用偏移；仅对缩放后的中文/其他字符应用偏移
            if typ == 'digit':
                dy = 0
                
        # 绘制：origin_y 是顶部起点，我们需要把 anchor 换回默认(左上角)，配合 dy 控制高度
        # 把 anchor="ls" 变成左上角定位，方便控制顶部对齐
        draw.text((x, origin_y + dy - bbox[1]), seg_text, font=font, fill=fill, anchor="ls")
        
        x += bbox[2] - bbox[0]
        
    return x


# ============ 主函数 ============
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
    resolved_font_path = font_path if (font_path and os.path.exists(font_path)) else None
    if resolved_font_path is None:
        print("警告: 未找到指定字体文件，正在使用默认字体。")

    if match_digit_height:
        segments, base_font, target_h = build_segment_fonts(text, resolved_font_path, font_size)
    else:
        try:
            base_font = ImageFont.truetype(resolved_font_path, font_size) if resolved_font_path \
                else ImageFont.load_default()
        except Exception:
            base_font = ImageFont.load_default()
        segments = [(text, 'other', base_font)]
        target_h = 0

    # 2. 测量整体 bbox
    total_w = 0
    top_min = 0
    bottom_max = 0
    for seg_text, typ, font in segments:
        if not seg_text:
            continue
        b = font.getbbox(seg_text, anchor="ls")
        total_w += (b[2] - b[0])
        top_min = min(top_min, b[1])
        bottom_max = max(bottom_max, b[3])

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

    # 整体文本的顶部 Y 坐标
    top_y = pad_total - top_min
    first_b = segments[0][2].getbbox(segments[0][0], anchor="ls") if segments[0][0] else (0, 0, 0, 0)
    start_x = pad_total - first_b[0]

    # 注意这里传入 top_y (作为起点) 和 target_h 用于对齐计算
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
    safe_text = re.sub(r'[\\/*?:"<>|]', "", text).strip() or uuid.uuid4().hex[:8]
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
    output_dir = "/Volumes/西数4T外置/百度网盘默认下载/test"

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
        generate_text_image(
            text=text,
            output_dir=output_dir,
            config=config
        )
    print("\n✅ 所有任务执行完成！")