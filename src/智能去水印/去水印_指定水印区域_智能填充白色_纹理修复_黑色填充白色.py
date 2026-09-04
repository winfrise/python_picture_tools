import cv2
import numpy as np
import os, sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import batch_process_file_with_callback

from plugins.smart_fill_watermark import smart_fill_watermark

def remove_gray_watermark(
    input_path,
    output_path,
    watermark_area_img=None,
    gray_range=(130, 220),
    dilate_size=3,
    is_smart_fill=True,
):
    start_time = time.time()

    print(f"--正在处理图片:{input_path}")

    
    # 读取输入图片
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"无法读取输入图片: {input_path}")
    
    h, w = img.shape[:2]
    
    # 初始化 area_mask
    area_mask = np.ones((h, w), dtype=np.uint8) * 255 # 默认整图都算水印区域
    
    # 处理水印区域图片
    if watermark_area_img:
        area_img = cv2.imread(watermark_area_img, cv2.IMREAD_UNCHANGED)
        
        if area_img & area_img.shape[-1] == 4:
            # 提取 alpha 通道
            alpha = area_img[:, :, 3]
            area_mask_raw = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)[1]
            # 【关键修复】缩放到输入图片尺寸
            area_mask = cv2.resize(area_mask_raw, (w, h))
            print(f"[INFO] 水印区域图片已加载，原始尺寸: {area_img.shape[:2]}, 缩放至: ({h}, {w})")


    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 灰度范围检测
    gray_range_mask = cv2.inRange(gray, gray_range[0], gray_range[1])
    
    # 灰度检测与区域限制的交集
    combined = cv2.bitwise_and(gray_range_mask, area_mask)
    
    # 膨胀
    kernel = np.ones((dilate_size, dilate_size), np.uint8)
    final_mask = cv2.dilate(combined, kernel, iterations=1)
    
    
    # 填充
    if is_smart_fill:
        result = smart_fill_watermark(img, final_mask) # 智能填充
    else:
        result = img.copy()
        result[final_mask > 0] = [255, 255, 255]  # 填充白色
    
    # 保存结果
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, result)
    

    end_time = time.time()
    print(f"运行耗时: {end_time - start_time:.4f} 秒")

    
    return result


if __name__ == "__main__":

    INPUT_PATH = "/Users/teacher/Desktop/20260830/0902钢板去水印/333/组合 1_页面_180.jpg"
    WATERMARK_AREA_IMG = None
    GRAY_RANGE = (160, 230)
    DILATE_SIZE = 3  # 膨胀
    IS_SMART_FILL = True

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
            gray_range=GRAY_RANGE,
            dilate_size=DILATE_SIZE,
            is_smart_fill=IS_SMART_FILL,
        )
    elif os.path.isdir(INPUT_PATH):
        def callback_func(input_file, output_file):
            remove_gray_watermark(
                input_path=input_file,
                output_path=output_file,
                watermark_area_img=WATERMARK_AREA_IMG,
                gray_range=GRAY_RANGE,
                dilate_size=DILATE_SIZE,
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