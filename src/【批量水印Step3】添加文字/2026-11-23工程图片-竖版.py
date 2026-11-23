from datetime import datetime
import random
from datetime import datetime, timedelta

from draw_text_on_image_steps import (
    draw_texts_on_image
)
# 测试与示例
# ============================================================
if __name__ == "__main__":
    from plugins.get_font_path import get_font_path


    input_dir = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/竖版图片_统一尺寸_加水印模板"
    output_dir = f"{input_dir}_加文字"
    work_root = f"{input_dir}_temp_watermarks"
    try_run = False


    def generate_random_time_in_slots(base_date_str):
        """
        根据输入的日期字符串，随机生成指定时间段内的时间并拼接。
        时间段：
        1. 10:00 - 11:30
        2. 14:30 - 15:30
        """
        # 1. 解析传入的日期字符串 (例如 "2026年09月14日")
        # 注意：这里假设输入已经是格式化好的日期字符串，如果输入是路径，需先提取日期部分
        try:
            dt = datetime.strptime(base_date_str, "%Y年%m月%d日")
        except ValueError:
            # 如果传入的是已经处理好的 "2026.09.14" 格式，则尝试该格式
            dt = datetime.strptime(base_date_str, "%Y.%m.%d")

        # 2. 定义两个时间段（以分钟为单位计算偏移量）
        # 时间段 A: 10:00 ~ 11:30 (共 90 分钟)
        slot_a_start = 10 * 60      # 10:00 = 600分钟
        slot_a_duration = 90        # 持续90分钟

        # 时间段 B: 14:30 ~ 15:30 (共 60 分钟)
        slot_b_start = 14 * 60 + 30 # 14:30 = 870分钟
        slot_b_duration = 60        # 持续60分钟

        # 3. 随机选择一个时间段 (50% 概率选 A 或 B)
        if random.random() < 0.5:
            # 选中时间段 A
            random_minutes = random.randint(0, slot_a_duration - 1)
            total_minutes = slot_a_start + random_minutes
        else:
            # 选中时间段 B
            random_minutes = random.randint(0, slot_b_duration - 1)
            total_minutes = slot_b_start + random_minutes

        # 4. 将分钟数转换为 timedelta 并加到日期上
        time_delta = timedelta(minutes=total_minutes)
        final_dt = dt + time_delta

        # 5. 格式化输出：日期 + 时间 (例如: 2026.09.14 10:25:33)
        # 如果你只需要日期点分格式，不需要时间，请把下面的格式改回去
        return final_dt.strftime("%Y.%m.%d %H:%M")


    # 通过路径提取【工作内容】
    def extract_work_content_from_path(img_path):
        base_str = input_dir
        name = img_path.replace(base_str, "").split('/')[1]
        return name


    # 通过路径提取【日期】
    def extract_date_from_path(img_path):
        base_str = input_dir
        date_str = img_path.replace(base_str, "").split('/')[2]

        # raw_date_from_path = datetime.strptime(date_str, "%Y年%m月%d日")
        result_time = generate_random_time_in_slots(date_str)

        return result_time


    common_config = {
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "text_color": "#000000",
        "match_digit_height": False,
        "blur_radius": 0.0,
    }

    text_items = [
        { # 项目名称
            "text": "河北承德围场300MW风储氢一体化项目",
            "font_size": 44,
            "text_color": "#ffffff",
            "offset_left": 240,
            "offset_bottom": 345,
        },
        { # 工作内容
            "text": extract_work_content_from_path,
            "font_size": 41,
            "offset_left": 902,
            "offset_bottom": 242,
            "blur_radius": 0.5,
            "width_ratio": 0.9,
            "height_ratio": 1.0
        },
        { # 日期
            "text": extract_date_from_path,
            "font_size": 44,
            "offset_left": 902,
            "offset_bottom": 66,
            "blur_radius": 0.5,
            "width_ratio": 0.9,
            "height_ratio": 1.0
        }
    ]

    draw_texts_on_image(
        image_path=input_dir,
        text_items=text_items,
        work_root=work_root,
        common_config=common_config,
        output_dir=output_dir,
        keep_work_dir=True, 
        try_run = try_run
    )