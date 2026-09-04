import cv2

import os, sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import batch_process_file_with_callback

from plugins.calculate_watermark_mask import calculate_watermark_mask
from plugins.fill_watermark_smart import fill_watermark_smart
from plugins.fill_watermark_white import fill_watermark_white

def remove_gray_watermark(
    input_path,
    output_path,
    watermark_area_img=None,
    is_smart_fill=True,
):
    start_time = time.time()

    print(f"--正在处理图片:{input_path}")

    # 读取输入图片
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"无法读取输入图片: {input_path}")

    # 计算水印区域掩码
    final_mask = calculate_watermark_mask(img, watermark_area_img)

    # 填充
    if is_smart_fill:
        result = fill_watermark_smart(img, final_mask)  # 智能填充
    else:
        result = img.copy()
        result = fill_watermark_white(result, final_mask)  # 智能填充

    # 保存结果
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, result)

    end_time = time.time()
    print(f"运行耗时: {end_time - start_time:.4f} 秒")

    return result


if __name__ == "__main__":

    INPUT_PATH = "/Users/teacher/Desktop/20260830/0902钢板去水印/test/001.jpg"
    WATERMARK_AREA_IMG = "/Users/teacher/Desktop/20260830/0902钢板去水印/test/mask.png"
    # WATERMARK_AREA_IMG = None
    IS_SMART_FILL = False

    # dark_threshold
    # 20 ~ 40（极暗/纯黑）：只识别接近纯黑的颜色。如果你的背景是深灰、深蓝或深红，它们不会被判定为黑色。
    # 50（默认推荐）：能识别大部分常见的黑色和非常深的灰色。
    # 60 ~ 80（深灰/暗色）：如果你的背景是深灰色、暗色木纹等，建议设置在这个范围。
    # 100+（中灰偏暗）：不建议设置这么高，否则普通的阴影或中等深度的颜色都会被误判为黑色，导致大面积被强制填充为白色。

    if os.path.isfile(INPUT_PATH):
        base_name, ext = os.path.splitext(INPUT_PATH)
        output_path = f"{base_name}_output_智能填充{ext}"

        remove_gray_watermark(
            input_path=INPUT_PATH,
            output_path=output_path,
            watermark_area_img=WATERMARK_AREA_IMG,
            is_smart_fill=IS_SMART_FILL,
        )
    elif os.path.isdir(INPUT_PATH):
        def callback_func(input_file, output_file):
            remove_gray_watermark(
                input_path=input_file,
                output_path=output_file,
                watermark_area_img=WATERMARK_AREA_IMG,
                is_smart_fill=IS_SMART_FILL,
            )

        output_dir = f"{INPUT_PATH}_output_智能去水印"
        batch_process_file_with_callback(
            input_dir=INPUT_PATH,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"路径错误: {INPUT_PATH}")