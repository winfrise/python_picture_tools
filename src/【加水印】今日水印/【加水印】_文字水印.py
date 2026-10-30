from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
import os,sys
import random
from datetime import datetime, timedelta
from tools.generate_random_time_str import generate_random_time_str
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback



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


def add_texts_to_image(input_path, output_path, text, config=None):
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
    blur_radius = config.get("blur_radius", 0) 


    if callable(text):
        text = text()

    # 确保最终拿到的是字符串
    if not isinstance(text, str):
        text = str(text)

    base = Image.open(input_path).convert("RGBA")
    img_width, img_height = base.size


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



    bbox = draw.textbbox((0, 0), text, font=font)
    text_h = bbox[3] - bbox[1]
    y = img_height - margin_bottom - text_h - bbox[1]
    x = margin_left

    if y < -text_h or y > img_height:
        print(f"警告: 文本 '{text}' 的坐标 y={y} 可能在画布外！")

    draw.text((x, y), text, font=font, fill=fill_color)

    # 【新增】对文字图层做高斯模糊（只模糊文字，背景不受影响）
    if blur_radius and blur_radius > 0:
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        # print(f"已对文字图层应用高斯模糊: radius={blur_radius}")

    result = Image.alpha_composite(base, text_layer)

    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg", ".bmp"):
        background = Image.new("RGB", result.size, (255, 255, 255))
        background.paste(result, mask=result.split()[3])
        background.save(output_path)
        # print(f"注意: {ext} 不支持透明，已合成到白色背景保存。")
    else:
        result.save(output_path)



# ================= 动态文字函数 =================
def random_time_near(base_time_str, hours_range=2, fmt="%Y-%m-%d %H:%M:%S"):
    base = datetime.strptime(base_time_str, fmt)
    delta_seconds = int(timedelta(hours=hours_range).total_seconds())
    rand_seconds = random.randint(-delta_seconds, delta_seconds)
    return (base + timedelta(seconds=rand_seconds)).strftime(fmt)





# def gen_time_text():
#     BASE_TIME = "2026.09.23 13:06"
#     time_str = random_time_near(BASE_TIME, hours_range=2, fmt="%Y.%m.%d %H:%M")
#     return f"{time_str}"

def gen_time_text():
    random_time = generate_random_time_str(
        start_date_str="2026-08-12",
        end_date_str="2026-08-25",
        start_hour=9,
        end_hour=17
    )
    return random_time



# ================= 测试调用示例 =================
if __name__ == "__main__":
    input_path = "/Volumes/西数4T外置/百度网盘默认下载/37张图片/8月10日——8月25日"

    text = gen_time_text

    config = {
        "font_size": 37+1, # 会比ps字体小1-2个像素
        "font_path": "/Users/teacher/Library/Fonts/微软雅黑.ttf",
        "color": "#000000",
        "opacity": 255,
        "margin_left": 260,
        "margin_bottom": 658,
        "line_spacing": 6,
        "blur_radius": 0.8,      # 【新增】高斯模糊半径：0=不模糊，1~3=轻微柔化，5+=明显雾化
    }

    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output{ext}"
        add_texts_to_image(
            input_path=input_path,
            output_path=output_path,
            text=text,
            config=config
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            add_texts_to_image(
                input_path=input_file,
                output_path=output_file,
                text=text,
                config=config
            )

        input_dir = input_path
        base_name, ext = os.path.splitext(input_path)
        output_dir = f"{base_name}_output"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func = callback_func,
        )
    else:
        print(f"【错误】：输入路径既不是文件也不是目录 -> {input_path}")