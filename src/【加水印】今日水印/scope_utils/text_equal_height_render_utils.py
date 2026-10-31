# text_render_common.py
"""
公共文字渲染逻辑：
- 文本按数字/其他字符分段
- 以数字像素高度为基准，归一化中文字号
- 垂直居中对齐渲染
"""
import os
import re
import uuid
from PIL import Image, ImageDraw, ImageFont


# ============ 文本分段 ============
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


# ============ 高度测量 ============
def measure_pixel_height(text, font):
    """返回文字实际渲染的像素高度（含上下伸部）。"""
    if not text:
        return 0
    bbox = font.getbbox(text)
    return max(1, bbox[3] - bbox[1])


# ============ 字体构建 / 高度归一化 ============
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


# ============ 渲染到画布 ============
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

        bbox = font.getbbox(seg_text, anchor="ls")

        dy = 0
        if target_h > 0:
            seg_h = bbox[3] - bbox[1]
            dy = (target_h - seg_h) / 2.0
            if typ == 'digit':
                dy = 0

        draw.text((x, origin_y + dy - bbox[1]), seg_text, font=font, fill=fill, anchor="ls")
        x += bbox[2] - bbox[0]

    return x


# ============ 测量整体 bbox ============
def measure_text_block(segments):
    """
    测量整体文本块的宽度和高度。
    返回 (total_w, top_min, bottom_max)，其中 top_min 通常 <= 0，bottom_max 通常 > 0。
    """
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
    return total_w, top_min, bottom_max


# ============ 解析字体配置 ============
def resolve_font_path(font_path):
    """如果字体文件不存在，返回 None 并使用默认字体。"""
    resolved = font_path if (font_path and os.path.exists(font_path)) else None
    if resolved is None:
        print("警告: 未找到指定字体文件，正在使用默认字体。")
    return resolved


def load_base_font(font_path, size):
    """直接加载基础字体（不做高度归一化时使用）。"""
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    return ImageFont.load_default()


# ============ 生成安全的文件名 ============
def safe_filename(text):
    s = re.sub(r'[\\/*?:"<>|]', "", text).strip()
    return s or uuid.uuid4().hex[:8]