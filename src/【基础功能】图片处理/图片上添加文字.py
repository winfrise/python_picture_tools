from PIL import Image, ImageDraw, ImageFont
import os

def add_texts_to_image(input_path, output_path, texts_config):
    """
    在图片上添加多个文本，支持负数坐标
    """
    # 1. 打开图片并转换为 RGB 模式（解决 KeyError: 'RGBA' 问题）
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入图片: {input_path}")

    image = Image.open(input_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    img_width, img_height = image.size
    print(f"图片尺寸: {img_width} x {img_height}")

    for i, item in enumerate(texts_config):
        text = item.get("text", "")
        x = item.get("x", 0)
        y = item.get("y", 0)
        font_size = item.get("font_size", 100)
        color = item.get("color", "red")  # 【修改】默认改为红色，防止看不见
        font_path = item.get("font_path", None)

        # 2. 加载字体
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 如果没指定字体，尝试使用系统默认字体，并放大一点以防看不见
                font = ImageFont.load_default()
                # 注意：load_default 在某些旧版本不支持 size 参数，可能需要手动处理
                print("警告: 未找到指定字体文件，正在使用默认字体。")
        except Exception as e:
            print(f"字体加载失败: {e}，使用默认字体。")
            font = ImageFont.load_default()

        # 3. 计算文本尺寸 (用于辅助定位，虽然这里主要用 anchor 或直接坐标)
        # 如果是新版 Pillow，可以用 textbbox
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 4. 【核心修复】处理负数坐标逻辑
        final_x = x
        final_y = y

        if x < 0:
            # 负数表示从右侧往左算
            final_x = img_width + x
            # 如果还需要考虑文字本身的宽度（即右对齐），可以减去 text_w
            # final_x = img_width + x - text_w
            print(f"文本 '{text}' X轴负数修正: {x} -> {final_x}")

        if y < 0:
            # 负数表示从底部往上算
            final_y = img_height + y
            # 如果需要底对齐，可以减去 text_h
            # final_y = img_height + y - text_h
            print(f"文本 '{text}' Y轴负数修正: {y} -> {final_y}")

        # 5. 边界检查（可选，防止画出界）
        if final_x < -text_w or final_x > img_width or final_y < -text_h or final_y > img_height:
             print(f"警告: 文本 '{text}' 的坐标 ({final_x}, {final_y}) 可能在画布外！")

        # 6. 绘制文字
        draw.text((final_x, final_y), text, font=font, fill=color)
        print(f"已绘制: '{text}' at ({final_x}, {final_y}), Color: {color}")

    # 保存图片
    image.save(output_path)
    print(f"处理完成，已保存至: {output_path}")


def batch_add_texts_to_image(input_dir, output_dir, texts_config):
    if not os.path.exists(input_dir):
        print(f"错误：输入文件夹不存在 -> {input_dir}")
        return

    # 2. 如果输出目录不存在，则自动创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"已自动创建输出文件夹：{output_dir}")


    # 4. 遍历输入文件夹中的所有文件
    file_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            # --- 过滤 macOS 自动生成的 ._ 开头文件 ---
            if file.startswith('._'):
                continue

            if file.lower().endswith(file_extensions):
                input_path = os.path.join(root, file)
                output_path = os.path.join(output_dir, file)

                add_texts_to_image(
                    input_path=input_path, 
                    output_path=output_path, 
                    texts_config=texts_config
                )


    print(f"\n🎉 批量任务完成！")
# ================= 测试调用示例 ================= 
if __name__ == "__main__":
    # 调用函数 (请替换为真实的图片路径)
    input_path = "/Users/teacher/Desktop/未命名文件夹 3/思凡尼2026图册_图片"


    texts_config = [
        {
            "text": "左上角文本",
            "x": 20, 
            "y": 20, 
            "font_size": 400, 
            "font_path": "/Users/teacher/Library/Fonts/SourceHanSerifSC-Bold.otf",
            "color": "yellow"
        },
        {
            "text": "右下角文本",
            "x": -20,  # 负数：距离右侧边缘 20 像素
            "y": -20,  # 负数：距离底部边缘 20 像素
            "font_size": 300, 
            "font_path": "/Users/teacher/Library/Fonts/SourceHanSerifSC-Bold.otf",
            "color": "red"
        },
        {
            "text": "右上角文本",
            "x": -150, # 负数：从右侧向左 150 像素
            "y": 50, 
            "font_path": "/Users/teacher/Library/Fonts/SourceHanSerifSC-Bold.otf",
            "color": "cyan"
        }
    ]


    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output{ext}"

        add_texts_to_image(
            input_path=input_path, 
            output_path=output_path, 
            texts_config=texts_config
        )
    elif os.path.isdir(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_dir = f"{base_name}_output"
        batch_add_texts_to_image(
            input_dir=input_path, 
            output_dir=output_dir, 
            texts_config=texts_config
        )
    else:
        print(f"【错误】：输入路径既不是文件也不是目录 -> {input_path}")

