from PIL import Image, ImageDraw, ImageFont
import os

def add_texts_to_image(input_path, output_path, texts_list, config=None):
    """
    在图片上添加多行文字，从下往上排列
    texts_list: 文字列表，最后一项在左下角最下面，依次向上排列
    config: 可选配置字典，包含 font_size, font_path, color, margin 等
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入图片: {input_path}")

    # 默认配置
    if config is None:
        config = {}
    font_size = config.get("font_size", 100)
    color = config.get("color", "red")
    font_path = config.get("font_path", None)
    margin_left = config.get("margin_left", 20)      # 距离左边距
    margin_bottom = config.get("margin_bottom", 20)      # 距离底部/行间距
    line_spacing = config.get("line_spacing", 10)  # 行间距额外像素

    image = Image.open(input_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    img_width, img_height = image.size
    print(f"图片尺寸: {img_width} x {img_height}")

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

    # 计算每行文字的高度（用一行文字测量）
    sample_bbox = draw.textbbox((0, 0), "测试Ag", font=font)
    line_height = sample_bbox[3] - sample_bbox[1]
    # 单行总占用高度 = 文字高度 + 行间距
    row_height = line_height + line_spacing

    # 从最后一行（左下角最下面）开始往上画
    # texts_list 顺序：列表第0项在最上面，最后一项在最下面
    # 所以倒序遍历，从最后一项开始画
    total_lines = len(texts_list)
    for i in range(total_lines - 1, -1, -1):
        text = texts_list[i]
        if text is None or text == "":
            continue

        # 计算该行文字应该在哪：越靠后的项（索引越大）越靠下
        # 最后一项 i = total_lines-1 画在最下面
        # 第 i 项距离底部的偏移 = (total_lines - 1 - i) * row_height + margin_bottom
        offset_from_bottom = (total_lines - 1 - i) * row_height + margin_bottom

        # 计算 y 坐标（左上角为原点，需要减去文字本身高度来对齐底部）
        bbox = draw.textbbox((0, 0), text, font=font)
        text_h = bbox[3] - bbox[1]
        # 使用 bbox[1] 作为偏移，让文字基线正确对齐
        y = img_height - offset_from_bottom - text_h - bbox[1]

        x = margin_left

        # 边界检查
        if y < -text_h or y > img_height:
            print(f"警告: 文本 '{text}' 的坐标 y={y} 可能在画布外！")

        draw.text((x, y), text, font=font, fill=color)
        print(f"已绘制: '{text}' at ({x}, {y})")

    image.save(output_path)
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

    # 文字列表：列表第0项在最上面，最后一项在最下面（左下角）
    texts_list = [
        "经度：112.510967",
        "纬度：22.399309",
        "时间：2026-09-28 10:50:46",
        "备注：茂名化州平定木浪村北",
    ]

    # 统一配置
    config = {
        "font_size": 25,
        # "font_path": "/Users/teacher/Library/Fonts/SourceHanSerifSC-Bold.otf",
        "font_path": "/Users/teacher/Library/Fonts/微软雅黑.ttf", # 微软雅黑
        "color": "#ffffff",
        "margin_left": 23,       # 距离左边距
        "margin_bottom": 37,       # 距离底部边距
        "line_spacing": 6,   # 行间距
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