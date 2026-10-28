from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
import os
import random
from datetime import datetime, timedelta


def _parse_color(color, opacity):
    """颜色 + 透明度 -> (R, G, B, A)"""
    if isinstance(color, str):
        rgba = ImageColor.getrgb(color)
    elif isinstance(color, (tuple, list)):
        rgba = tuple(color)
    else:
        raise ValueError(f"不支持的颜色格式: {color}")

    if len(rgba) == 3:
        r, g, b = rgba
        a = 255
    else:
        r, g, b, a = rgba

    if opacity is not None:
        if isinstance(opacity, float) and 0.0 <= opacity <= 1.0:
            a = int(a * opacity)
        else:
            a = int(max(0, min(255, opacity)))
    return (r, g, b, a)


def _resolve_text(item):
    """
    将 texts_list 中的一项解析为字符串：
    - 字符串：直接返回
    - 函数：调用并返回结果
    - 字典：取 "func"（优先）或 "text"
    """
    if callable(item):
        return str(item())
    if isinstance(item, dict):
        if "func" in item and callable(item["func"]):
            return str(item["func"]())
        return str(item.get("text", ""))
    if item is None:
        return ""
    return str(item)


def add_texts_to_image(input_path, output_path, texts_list, config=None):
    """
    在图片上添加多行文字，从下往上排列，支持半透明、动态文字、高斯模糊
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入图片: {input_path}")

    if config is None:
        config = {}
    font_size = config.get("font_size", 100)
    color = config.get("color", "red")
    opacity = config.get("opacity", 128)
    font_path = config.get("font_path", None)
    margin_left = config.get("margin_left", 20)
    margin_bottom = config.get("margin_bottom", 20)
    line_spacing = config.get("line_spacing", 10)
    blur_radius = config.get("blur_radius", 0)      # 【新增】高斯模糊半径，0 表示不模糊

    base = Image.open(input_path).convert("RGBA")
    img_width, img_height = base.size
    print(f"图片尺寸: {img_width} x {img_height}")

    text_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # 加载字体
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
            print("警告: 未找到指定字体文件，正在使用默认字体。")
    except Exception as e:
        print(f"字体加载失败: {e}，使用默认字体。")
        font = ImageFont.load_default()

    fill_color = _parse_color(color, opacity)
    print(f"文字颜色(含透明度): {fill_color}")

    resolved_texts = [_resolve_text(item) for item in texts_list]

    sample_bbox = draw.textbbox((0, 0), "测试Ag", font=font)
    line_height = sample_bbox[3] - sample_bbox[1]
    row_height = line_height + line_spacing

    total_lines = len(resolved_texts)
    for i in range(total_lines - 1, -1, -1):
        text = resolved_texts[i]
        if text is None or text == "":
            continue

        offset_from_bottom = (total_lines - 1 - i) * row_height + margin_bottom

        bbox = draw.textbbox((0, 0), text, font=font)
        text_h = bbox[3] - bbox[1]
        y = img_height - offset_from_bottom - text_h - bbox[1]
        x = margin_left

        if y < -text_h or y > img_height:
            print(f"警告: 文本 '{text}' 的坐标 y={y} 可能在画布外！")

        draw.text((x, y), text, font=font, fill=fill_color)
        print(f"已绘制: '{text}' at ({x}, {y})")

    # 【新增】对文字图层做高斯模糊（只模糊文字，背景不受影响）
    if blur_radius and blur_radius > 0:
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        print(f"已对文字图层应用高斯模糊: radius={blur_radius}")

    result = Image.alpha_composite(base, text_layer)

    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg", ".bmp"):
        background = Image.new("RGB", result.size, (255, 255, 255))
        background.paste(result, mask=result.split()[3])
        background.save(output_path)
        print(f"注意: {ext} 不支持透明，已合成到白色背景保存。")
    else:
        result.save(output_path)

    print(f"处理完成，已保存至: {output_path}")


def batch_add_texts_to_image(input_dir, output_dir, texts_list, config=None):
    if not os.path.exists(input_dir):
        print(f"错误：输入文件夹不存在 -> {input_dir}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"已自动创建输出文件夹：{output_dir}")

    file_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.startswith('._'):
                continue
            if file.lower().endswith(file_extensions):
                input_path = os.path.join(root, file)
                output_path = os.path.join(output_dir, file)
                add_texts_to_image(
                    input_path=input_path,
                    output_path=output_path,
                    texts_list=texts_list,
                    config=config
                )

    print(f"\n🎉 批量任务完成！")


# ================= 动态文字函数 =================
def random_time_near(base_time_str, hours_range=2, fmt="%Y-%m-%d %H:%M:%S"):
    base = datetime.strptime(base_time_str, fmt)
    delta_seconds = int(timedelta(hours=hours_range).total_seconds())
    rand_seconds = random.randint(-delta_seconds, delta_seconds)
    return (base + timedelta(seconds=rand_seconds)).strftime(fmt)





def gen_time_text():
    BASE_TIME = "2026.09.23 13:06"
    time_str = random_time_near(BASE_TIME, hours_range=2, fmt="%Y.%m.%d %H:%M")
    return f"{time_str}"


# ================= 测试调用示例 =================
if __name__ == "__main__":
    input_path = "/Users/teacher/Downloads/Canvas_20261028_14时30分54秒/001_output_图片覆盖"

    texts_list = [
        gen_time_text
    ]

    config = {
        "font_size": 42+1, # 会比ps字体小1-2个像素
        "font_path": "/Users/teacher/Library/Fonts/微软雅黑.ttf",
        "color": "#ffffff",
        "opacity": 255,
        "margin_left": 290,
        "margin_bottom": 300,
        "line_spacing": 6,
        "blur_radius": 0,      # 【新增】高斯模糊半径：0=不模糊，1~3=轻微柔化，5+=明显雾化
    }

    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output{ext}"
        add_texts_to_image(
            input_path=input_path,
            output_path=output_path,
            texts_list=texts_list,
            config=config
        )
    elif os.path.isdir(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_dir = f"{base_name}_output"
        batch_add_texts_to_image(
            input_dir=input_path,
            output_dir=output_dir,
            texts_list=texts_list,
            config=config
        )
    else:
        print(f"【错误】：输入路径既不是文件也不是目录 -> {input_path}")