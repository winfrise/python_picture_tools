import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_watermark_pipeline import run_watermark_pipeline
from helpers.color_to_gray import color_to_gray
from helpers.hex_to_rgb import hex_to_rgb
from utils import batch_process_file_with_callback

# ================= 3. 测试运行 =================
if __name__ == "__main__":
    image_path = "/Users/teacher/Desktop/xxx/test11"
    pipeline_steps = [
        {
            "watermark_area_img": None,
            "target_gray": color_to_gray("#bcbeb9"),
            "target_gray_threshold": 30,
            # "fill_color": [255, 255, 255]
            "fill_color": hex_to_rgb("#d4ebdb")
        },
        {
            "watermark_area_img": None,
            "target_gray": color_to_gray("#757774"),
            "target_gray_threshold": 20,
            "exclude_rgb_list": [
                {
                    "color_rgb": hex_to_rgb("#4f9d73"),
                    "color_threshold": 50,
                }
            ],
            "fill_color": [0, 0, 0]
        },
    ]



    if os.path.isfile(image_path):
        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_output_智能填充{ext}"

        run_watermark_pipeline(image_path, pipeline_steps, output_path)
    elif os.path.isdir(image_path):
        input_dir = image_path
        def callback_func(input_file, output_file):
            run_watermark_pipeline(
                image_path=input_file,
                output_path=output_file,
                steps = pipeline_steps
            )

        output_dir = f"{input_dir}_output_智能去水印"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"路径错误: {image_path}")


