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
    生成文字透明 PNG，效果与「直接绘制到图片」完全一致：
    - 光栅化参数与 add_texts_to_image 相同
    - 模糊在带 padding 的画布上做（边界不被截断）
    - 拉伸在模糊之前/之后均可，但必须保持笔画粗细语义一致
    """
    if config is None:
        config = {}

    font_path    = config.get("font_path", "arial.ttf")
    font_size    = config.get("font_size", 40)
    padding      = config.get("padding", 20)          # 最终画布四周留白（透明）
    text_color   = config.get("text_color", "black")
    bg_color     = config.get("bg_color", (255, 255, 255, 0))
    width_ratio  = config.get("width_ratio", 1.0)
    height_ratio = config.get("height_ratio", 1.0)
    blur_radius  = config.get("blur_radius", 0)

    if callable(text):
        text = text()
    if not isinstance(text, str):
        text = str(text)

    # ---------- 1. 加载字体（与脚本1 完全一致） ----------
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
            print("警告: 未找到指定字体文件，正在使用默认字体。")
    except Exception as e:
        print(f"字体加载失败: {e}，使用默认字体。")
        font = ImageFont.load_default()

    # ---------- 2. 测量 bbox ----------
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    if bw <= 0 or bh <= 0:
        raise ValueError("文字尺寸为 0，请检查文本内容")

    # ---------- 3. 关键：为 blur 预留足够 padding ----------
    # 高斯模糊半径 r 需要 ≥ 4r 的透明余量，否则边界 alpha 会被截断削细
    # 再叠加用户 padding，保证"直接绘制"时大画布四周的透明余量
    blur_pad = int(max(0, blur_radius) * 6) + 2      # 模糊保护圈
    pad_total = padding + blur_pad                   # 最终画布的外边距

    canvas_w = bw + 2 * pad_total
    canvas_h = bh + 2 * pad_total

    # ---------- 4. 在足够大的画布上渲染文字（只光栅化一次） ----------
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (pad_total - bbox[0], pad_total - bbox[1]),
        text, font=font, fill=text_color
    )

    # ---------- 5. 在带 padding 的大画布上 blur（边界不截断） ----------
    if blur_radius and blur_radius > 0:
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # ---------- 6. 非等比拉伸（此时整张画布一起拉伸，与脚本1 行为一致） ----------
    # 脚本1 是先 resize 文字小图再 paste；这里整张画布 resize 等价于
    # "文字 + 其周围透明余量一起等比/非等比缩放"，字形像素映射与脚本1 相同
    if abs(width_ratio - 1.0) > 1e-6 or abs(height_ratio - 1.0) > 1e-6:
        new_w = max(1, int(round(canvas_w * width_ratio)))
        new_h = max(1, int(round(canvas_h * height_ratio)))
        canvas = canvas.resize((new_w, new_h), Image.LANCZOS)

    # ---------- 7. 保存 ----------
    safe_text = re.sub(r'[\\/*?:"<>|]', "", text).strip() or uuid.uuid4().hex[:8]
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{safe_text}.png")
    canvas.save(save_path)
    print(f"图片已生成: {save_path}  "
          f"(字形 {bw}x{bh}, 画布 {canvas.size[0]}x{canvas.size[1]}, blur={blur_radius})")
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
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "padding": 30,
        "text_color": "#000000",
        "bg_color": (255, 255, 255, 0),
        "width_ratio": 1.0,
        "height_ratio": 1.1,
        "blur_radius": 0.7,        # 新增：模糊半径，0 表示不模糊
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