from PIL import Image, ImageDraw, ImageFont, ImageColor
import os


def _parse_color(color, opacity):
    """
    颜色 + 透明度 -> (R, G, B, A)
    color: 支持 "red" / "#ffffff" / (255,0,0) / (255,0,0,128)
    opacity: 0~255 整数 或 0.0~1.0 浮点；None 表示使用颜色自带 alpha
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
    else:
        r, g, b, a = rgba

    if opacity is not None:
        if isinstance(opacity, float) and 0.0 <= opacity <= 1.0:
            a = int(a * opacity)
        else:
            a = int(max(0, min(255, opacity)))
    return (r, g, b, a)


def add_texts_to_image(input_path, output_path, texts_list, config=None):
    """
    在图片上添加多行文字，从下往上排列，支持半透明
    texts_list: 文字列表，最后一项在左下角最下面，依次向上排列
    config: 可选配置字典，包含 font_size, font_path, color, opacity, margin 等
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入图片: {input_path}")

    # 默认配置
    if config is None:
        config = {}
    font_size = config.get("font_size", 100)
    color = config.get("color", "red")
    opacity = config.get("opacity", 128)          # 【新增】默认半透明
    font_path = config.get("font_path", None)
    margin_left = config.get("margin_left", 20)
    margin_bottom = config.get("margin_bottom", 20)
    line_spacing = config.get("line_spacing", 10)

    # 【改动1】原图转 RGBA，才能做透明合成
    base = Image.open(input_path).convert("RGBA")
    img_width, img_height = base.size
    print(f"图片尺寸: {img_width} x {img_height}")

    # 【改动2】新建一张全透明图层，文字画在它上面
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

    # 【改动3】解析带 alpha 的填充色
    fill_color = _parse_color(color, opacity)
    print(f"文字颜色(含透明度): {fill_color}")

    # 计算每行文字的高度
    sample_bbox = draw.textbbox((0, 0), "测试Ag", font=font)
    line_height = sample_bbox[3] - sample_bbox[1]
    row_height = line_height + line_spacing

    total_lines = len(texts_list)
    for i in range(total_lines - 1, -1, -1):
        text = texts_list[i]
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

    # 【改动4】透明图层与底图 alpha 合成，透明度精确生效
    result = Image.alpha_composite(base, text_layer)

    # 【改动5】保存时处理不支持透明的格式
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg", ".bmp"):
        # 这些格式不支持透明，合成到白底
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


# ================= 测试调用示例 =================
if __name__ == "__main__":
    input_path = "/Users/teacher/Downloads/去水印_待加水印"

    texts_list = [
        "经度：112.510967",
        "纬度：22.399309",
        "时间：2026-09-28 10:50:46",
        "备注：茂名化州平定木浪村北",
    ]

    config = {
        "font_size": 25,
        "font_path": "/Users/teacher/Library/Fonts/微软雅黑.ttf",
        "color": "#ffffff",
        "opacity": 255,        # 【新增】半透明：128 ≈ 50%，可调 0~255 或 0.0~1.0
        "margin_left": 23,
        "margin_bottom": 37,
        "line_spacing": 6,
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