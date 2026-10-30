import os
import re
import uuid
from PIL import Image, ImageDraw, ImageFont


def generate_text_image(text, output_dir, config=None):
    """
    根据文本生成一张图片，画布大小自动适应文字尺寸。

    :param text: 字符串，要绘制到图片上的文本内容
    :param output_dir: 图片输出目录
    :param config: 配置字典，支持以下可选参数：
                   图片将以 RGBA 模式创建，背景默认为透明，保存为 PNG 格式
                   - font_path: 字体文件路径
                   - font_size: 字体大小 (默认 100)
                   - padding: 文字四周留白 (默认 20)
                   - text_color: 文字颜色 (默认 "black")
    """
    # 1. 处理配置项 (提供默认值)
    if config is None:
        config = {}

    font_path = config.get("font_path", None)
    font_size = config.get("font_size", 100)
    padding = config.get("padding", 20)
    text_color = config.get("text_color", "black")

    # 2. 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[INFO] 已创建输出目录: {output_dir}")

    # 3. 加载字体
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        print("[WARN] 未找到指定字体，使用默认字体（中文可能无法显示）")
        font = ImageFont.load_default()

    # 4. 使用文本内容作为文件名（清理非法字符）
    safe_text = re.sub(r'[\\/:*?"<>|,，。；：！！？]', '_', text)
    # 去除首尾下划线和空格
    safe_text = safe_text.strip('_').strip()
    if not safe_text:
        safe_text = str(uuid.uuid4())[:8]

    # 临时创建一个 Draw 对象来计算文字的真实边界
    temp_img = Image.new('RGBA', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)

    # 计算文字宽高
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 动态计算画布大小 (文字宽高 + 左右/上下 padding)
    img_width = text_width + padding * 2
    img_height = text_height + padding * 2

    # 创建真实尺寸的图片并绘制
    img = Image.new('RGBA', (img_width, img_height))
    draw = ImageDraw.Draw(img)

    # 将文字绘制在 padding 偏移处
    # 确保文字颜色适配 RGBA 模式
    if isinstance(text_color, tuple) and len(text_color) == 3:
        text_color_rgba = text_color + (255,)
    else:
        text_color_rgba = text_color
    draw.text((padding, padding), text, font=font, fill=text_color_rgba)

    # 保存图片，文件名使用文本内容
    save_path = os.path.join(output_dir, f"{safe_text}.png")
    img.save(save_path)
    print(f"[OK] 已生成: {save_path} | 尺寸: {img_width}x{img_height} | 内容: {text[:20]}...")


# ================= 测试代码 =================

# 自定义配置
my_config = {
    "font_path": "/Users/teacher/Library/Fonts/微软雅黑.ttf",
    "font_size": 40,
    "padding": 30,                # 四周留白 30px
    "text_color": "#333333"       # 深灰色文字
}

# 执行生成（每次只传入一个字符串，生成一张图片）
if __name__ == "__main__":
    generate_text_image(
        text="这是一段测试文本",
        output_dir="./my_output_images",
        config=my_config
    )