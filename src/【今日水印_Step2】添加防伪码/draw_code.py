import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def draw_text_with_shadow(
    image,
    text,
    output_path=None,
    x=0,
    y=0,
    font_size=40,
    font_color="white",
    font_path=None,
    shadow_color=(0, 0, 0, 180),
    shadow_offset=(4, 4),
    shadow_blur=6,
    anchor=None
):
    """
    单张图片文字绘制（带阴影）
    """

    text = text() if callable(text) else text
    # 1. 加载图片
    if isinstance(image, str):
        if not os.path.exists(image):
            raise FileNotFoundError(f"图片不存在: {image}")
        img = Image.open(image)
        is_path_input = True
    else:
        img = image.copy()
        is_path_input = False

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # 2. 加载字体
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            fallback_fonts = ["msyh.ttc", "simhei.ttf", "Arial.ttf", "PingFang.ttc"]
            font = None
            for f in fallback_fonts:
                try:
                    font = ImageFont.truetype(f, font_size)
                    break
                except IOError:
                    continue
            if font is None:
                font = ImageFont.load_default()
    except Exception as e:
        raise ValueError(f"字体加载失败: {e}")

    canvas_w, canvas_h = img.size

    # 3. 智能判断锚点 (Anchor)
    if anchor is None:
        if x >= 0 and y >= 0:
            anchor = "la"
        elif x < 0 and y >= 0:
            anchor = "ra"
        elif x >= 0 and y < 0:
            anchor = "ld"
        else:
            anchor = "rd"

    # 4. 坐标计算：处理负数
    real_x = x if x >= 0 else canvas_w + x
    real_y = y if y >= 0 else canvas_h + y

    # 5. 绘制阴影图层
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_x = real_x + shadow_offset[0]
    shadow_y = real_y + shadow_offset[1]
    shadow_draw.text((shadow_x, shadow_y), text, font=font, fill=shadow_color, anchor=anchor)

    if shadow_blur > 0:
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

    img = Image.alpha_composite(img, shadow_layer)

    # 6. 绘制主文字图层
    draw = ImageDraw.Draw(img)
    draw.text((real_x, real_y), text, font=font, fill=font_color, anchor=anchor)

    # 7. 保存输出
    if output_path and is_path_input:
        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        
        ext = os.path.splitext(output_path)[1].lower()
        save_img = img
        if ext in (".jpg", ".jpeg"):
            save_img = img.convert("RGB")
            
        save_img.save(output_path)
        
    return img


def batch_draw_text_with_shadow(
    input_dir,
    output_dir,
    text,
    x=0,
    y=0,
    font_size=40,
    font_color="white",
    font_path=None,
    shadow_color=(0, 0, 0, 180),
    shadow_offset=(4, 4),
    shadow_blur=6,
    anchor=None,
    exts=(".jpg", ".jpeg", ".png", ".bmp", ".webp"),
):
    """
    批量给文件夹内的图片绘制文字。
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"输入目录不存在: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)
    success_files = []

    for filename in sorted(os.listdir(input_dir)):
        # ---------------- 新增：跳过隐藏文件和临时文件 ----------------
        if filename.startswith(".") or filename.startswith("~$"):
            continue
        # -------------------------------------------------------------

        # 跳过非图片文件
        if not filename.lower().endswith(exts):
            continue

        src_path = os.path.join(input_dir, filename)
        dst_path = os.path.join(output_dir, filename)

        # 决定当前图片的文字内容
        current_text = text
        try:
            draw_text_with_shadow(
                image=src_path,
                text=current_text,
                output_path=dst_path,
                x=x, y=y,
                font_size=font_size,
                font_color=font_color,
                font_path=font_path,
                shadow_color=shadow_color,
                shadow_offset=shadow_offset,
                shadow_blur=shadow_blur,
                anchor=anchor
            )
            success_files.append(dst_path)
            print(f"[OK] 处理完成: {filename}")
        except Exception as e:
            print(f"[FAIL] 处理失败: {filename} | 错误: {e}")

    print(f"\n批量处理结束，成功 {len(success_files)} 张。")
    return success_files