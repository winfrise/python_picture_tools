"""文字渲染公共工具：字体加载、颜色解析、文字测量、拉伸模糊、文本解析。"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter


def _resolve_text(text):
    """如果 text 是可调用对象则调用，最终保证返回 str。"""
    if callable(text):
        text = text()
    if not isinstance(text, str):
        text = str(text)
    return text


def _load_font(font_path, font_size):
    """加载字体，找不到/失败时回退到默认字体。"""
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, font_size)
        print("警告: 未找到指定字体文件，正在使用默认字体。")
    except Exception as e:
        print(f"字体加载失败: {e}，使用默认字体。")
    return ImageFont.load_default()


def _parse_color(color, opacity=None):
    """
    颜色 + 透明度 -> (R, G, B, A)

    支持：
      - 颜色字符串："black" / "#000000" / "#00000080"
      - RGB 元组 (r, g, b)
      - RGBA 元组 (r, g, b, a)
    opacity：
      - float 0.0~1.0：按比例乘到现有 alpha 上
      - int   0~255  ：直接覆盖 alpha
      - None        ：使用颜色自带 alpha
    """
    if isinstance(color, str):
        rgba = ImageColor.getrgb(color)
    elif isinstance(color, (tuple, list)):
        rgba = tuple(color)
    else:
        raise ValueError(f"不支持的颜色格式: {color}")

    if len(rgba) == 3:
        r, g, b = rgba
        a = 255
    elif len(rgba) == 4:
        r, g, b, a = rgba
    else:
        raise ValueError(f"颜色元组长度必须为 3 或 4: {rgba}")

    if opacity is not None:
        if isinstance(opacity, float) and 0.0 <= opacity <= 1.0:
            a = int(a * opacity)
        else:
            a = int(max(0, min(255, opacity)))
    return (r, g, b, a)


def _measure_text(text, font):
    """
    测量文字 bbox 与宽高。
    Returns:
        (bbox, w, h)；尺寸为 0 时返回 (None, None, None)
    """
    measure_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    bbox = ImageDraw.Draw(measure_img).textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    if w <= 0 or h <= 0:
        return None, None, None
    return bbox, w, h


def _stretch_image(img, width_ratio, height_ratio):
    """按宽高比例拉伸图像（Lanczos）。比例都为 1 时原样返回。"""
    if abs(width_ratio - 1.0) < 1e-6 and abs(height_ratio - 1.0) < 1e-6:
        return img
    new_w = max(1, int(round(img.width * width_ratio)))
    new_h = max(1, int(round(img.height * height_ratio)))
    return img.resize((new_w, new_h), Image.LANCZOS)


def _blur_image(img, blur_radius):
    """高斯模糊，半径 <=0 时原样返回。"""
    if blur_radius and blur_radius > 0:
        return img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return img


def _render_text_tight(text, font, fill_color,
                       width_ratio=1.0, height_ratio=1.0, blur_radius=0):
    """
    把文字渲染成紧贴字形的 RGBA 小图（先模糊再拉伸）。

    Returns:
        (text_img, bbox, raw_w, raw_h)；尺寸为 0 时 text_img 为 None
    """
    bbox, raw_w, raw_h = _measure_text(text, font)
    if bbox is None:
        return None, None, None, None

    text_img = Image.new("RGBA", (raw_w, raw_h), (0, 0, 0, 0))
    ImageDraw.Draw(text_img).text(
        (-bbox[0], -bbox[1]), text, font=font, fill=fill_color
    )
    text_img = _blur_image(text_img, blur_radius)
    text_img = _stretch_image(text_img, width_ratio, height_ratio)
    return text_img, bbox, raw_w, raw_h