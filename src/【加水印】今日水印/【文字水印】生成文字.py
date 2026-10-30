import os
import re
import uuid
from PIL import Image, ImageDraw, ImageFont


def generate_text_image(text, output_dir="./output", config=None):
    """
    生成单张文字图片。
    - width_ratio:  文字最终宽度 = 原始文字宽度 × width_ratio
    - height_ratio: 文字最终高度 = 原始文字高度 × height_ratio
    两者独立，通过对文字位图做非等比拉伸实现（可实现"只变高不变宽"）。
    """
    if config is None:
        config = {}

    font_path    = config.get("font_path", "arial.ttf")
    font_size    = config.get("font_size", 40)
    padding      = config.get("padding", 20)
    text_color   = config.get("text_color", "black")
    bg_color     = config.get("bg_color", "white")
    width_ratio  = config.get("width_ratio", 1.0)
    height_ratio = config.get("height_ratio", 1.0)


    if callable(text):
        text = text()
    
    # 确保最终拿到的是字符串
    if not isinstance(text, str):
        text = str(text)

    # 1. 载入字体
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    # 2. 测量原始文字尺寸（用 textbbox 得到真实像素边界）
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    if bw <= 0 or bh <= 0:
        raise ValueError("文字尺寸为 0，请检查文本内容")

    # 3. 把文字渲染到一张刚好包住它的透明小图上（用 bbox 偏移对齐）
    text_img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((-bbox[0], -bbox[1]), text, font=font, fill=text_color)

    # 4. 非等比拉伸到目标宽高（这就是"文字高 150%"的核心）
    target_w = max(1, int(round(bw * width_ratio)))
    target_h = max(1, int(round(bh * height_ratio)))
    text_img = text_img.resize((target_w, target_h), Image.LANCZOS)

    # 5. 画布 = 拉伸后的文字尺寸 + padding，并把文字居中贴上
    final_w = target_w + padding * 2
    final_h = target_h + padding * 2
    canvas = Image.new("RGBA", (final_w, final_h), bg_color)
    canvas.paste(text_img, (padding, padding), text_img)  # 用 alpha 做蒙版

    # 6. 保存
    safe_text = re.sub(r'[\\/*?:"<>|]', "", text).strip() or uuid.uuid4().hex[:8]
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{safe_text}.png")
    canvas.save(save_path)
    print(f"图片已生成: {save_path}  (文字 {bw}x{bh} -> {target_w}x{target_h})")
    return save_path


if __name__ == "__main__":
    test_config = {
        "font_path": "/Users/teacher/Library/Fonts/微软雅黑.ttf",
        "font_size": 40,
        "padding": 30,
        "text_color": "#333333",
        "bg_color": (255, 255, 255, 0),
        "width_ratio": 1.0,
        "height_ratio": 1.5,
        "fit_mode": "none",   # 关键：文字保持原大小，画布高 = 文字高 × 150%
    }
    generate_text_image("测试文字缩放", output_dir="./output", config=test_config)