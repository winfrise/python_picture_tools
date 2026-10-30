import os
import re
import uuid
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from tools.generate_random_time_str import generate_random_time_str

def get_font_path(font_name="苹方黑体-中粗-简.ttf"):
    """
    获取项目 assets/fonts 目录下字体的绝对路径。
    
    Args:
        font_name (str): 字体文件名，默认为 "苹方黑体-中粗-简.ttf"
        
    Returns:
        str: 字体的绝对路径字符串。如果文件不存在，返回 None 并打印警告。
    """
    # 1. 获取当前脚本所在的绝对目录
    # __file__ 指向当前代码所在的 .py 文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 向上回退一级到 src 目录，再进入 assets/fonts
    # 假设当前文件在 src/某文件夹/ 下，所以需要 ".."
    font_dir = os.path.join(current_dir, "..", "assets", "fonts")
    
    # 3. 规范化路径（消除 .. 符号）并拼接文件名
    full_path = os.path.normpath(os.path.join(font_dir, font_name))
    
    # 4. 检查文件是否存在
    if os.path.exists(full_path):
        return full_path
    else:
        print(f"⚠️ 警告：未找到字体文件 -> {full_path}")
        return None



def generate_text_image(text, output_dir="./output", config=None):
    """
    生成单张文字图片。
    - width_ratio:  文字最终宽度 = 原始文字宽度 × width_ratio
    - height_ratio: 文字最终高度 = 原始文字高度 × height_ratio
    两者独立，通过对文字位图做非等比拉伸实现（可实现"只变高不变宽"）。
    - blur_radius:  文字模糊半径（高斯模糊），0 表示不模糊
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
    blur_radius  = config.get("blur_radius", 0)      # 新增：模糊半径

    if callable(text):
        text = text()

    # 确保最终拿到的是字符串
    if not isinstance(text, str):
        text = str(text)

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

    # 4.1 对文字做模糊处理（在拉伸之后做，模糊效果才会跟随缩放一致）
    if blur_radius and blur_radius > 0:
        text_img = text_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

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
    print(f"图片已生成: {save_path}  "
          f"(文字 {bw}x{bh} -> {target_w}x{target_h}, blur={blur_radius})")
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
    output_dir = "/Volumes/西数4T外置/百度网盘默认下载/37张图片/8月10日——8月25日_完成/01"

    config = {
        "font_path": get_font_path("苹方黑体-中黑-简.ttf"),
        "font_size": 35,
        "padding": 30,
        "text_color": "#000000",
        "bg_color": (255, 255, 255, 0),
        "width_ratio": 1.0,
        "height_ratio": 1.1,
        "blur_radius": 0.8,        # 新增：模糊半径，0 表示不模糊
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