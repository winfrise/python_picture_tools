import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_watermark_pipeline import run_watermark_pipeline
from helpers.color_to_gray import color_to_gray
from helpers.hex_to_rgb import hex_to_rgb

# ================= 3. 测试运行 =================
if __name__ == "__main__":
    image_path = "/Users/teacher/Desktop/青岛大学附属医院总务设备采购项目002(二次)-证书-测试/证书/test11/青岛大学_页面_009.jpg"
    pipeline_steps = [
        {
            "watermark_target_gray": color_to_gray("#bcbeb9"),
            "watermark_gray_tolerance": 30,
            "watermark_area_img": None,
            # "fill_color": [255, 255, 255]
            "fill_color": hex_to_rgb("#d4ebdb")
        },
        {
            "watermark_area_img": None,
            "watermark_target_gray": color_to_gray("#767875"),
            "watermark_gray_tolerance": 20,
            "exclude_rgb_list": [
                {
                    "color_rgb": hex_to_rgb("#4f9d73"),
                    "color_threshold": 10
                },
                {
                    "color_rgb": hex_to_rgb("#089141"),
                    "color_threshold": 30
                }
            ],
            "fill_color": [255, 0, 0]
        },
    ]


    run_watermark_pipeline(image_path, pipeline_steps)

