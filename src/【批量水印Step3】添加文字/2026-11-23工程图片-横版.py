from datetime import datetime

from draw_text_on_image_steps import (
    draw_texts_on_image
)
# 测试与示例
# ============================================================
if __name__ == "__main__":
    from plugins.get_font_path import get_font_path


    input_dir = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/001_横版_竖版_分类/横版图片_统一尺寸_加水印模板"
    output_dir = f"{input_dir}_加文字"
    work_root = f"{input_dir}_temp_watermarks"
    try_run = False


    # 通过路径提取【工作内容】
    def extract_work_content_from_path(img_path):
        base_str = input_dir
        name = img_path.replace(base_str, "").split('/')[1]
        return name


    # 通过路径提取【日期】
    def extract_date_from_path(img_path):
        base_str = input_dir
        date_str = img_path.replace(base_str, "").split('/')[2]

        dt = datetime.strptime(date_str, "%Y年%m月%d日")

        # 转换成 点分隔，并补零 (输出: 2026.09.14)
        format_1 = dt.strftime("%Y.%m.%d")

        return format_1


    common_config = {
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "text_color": "#000000",
        "match_digit_height": True,
        "blur_radius": 0.0,
    }

    text_items = [
        { # 项目名称
            "text": "河北承德围场300MW风储氢一体化项目",
            "font_size": 28,
            "text_color": "#ffffff",
            "offset_left": 496,
            "offset_bottom": 159,
        },
        { # 工作内容
            "text": extract_work_content_from_path,
            "font_size": 24,
            "offset_left": 843,
            "offset_bottom": 94,
            "blur_radius": 0,
            "width_ratio": 0.9,
            "height_ratio": 1.0
        },
        { # 日期
            "text": extract_date_from_path,
            "font_size": 24,
            "offset_left": 843,
            "offset_bottom": 26,
            "blur_radius": 0,
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