import cv2
import numpy as np
import os,sys
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import batch_process_file_with_callback


def smart_fill_watermark(
        img, 
        final_mask, 
        surround_radius=5, 
        white_threshold=200, 
        dark_threshold_min=0, 
        dark_threshold_max = 150,
        dark_surround_fill_white=True
):
    """
    智能填充水印区域。
    根据水印周围的像素颜色，决定填充为白色还是周围最多的颜色。
    如果开启了 dark_surround_fill_white 且周围接近黑色较多，则强制填充白色。
    """
    result = img.copy()
    h, w = img.shape[:2]
    
    # 颜色量化，让直方图统计更稳定（每32个颜色值合并为一个桶）
    quantized_img = (img // 32) * 32
    
    # 获取所有需要填充的水印像素坐标
    ys, xs = np.where(final_mask > 0)
    
    # 用于调试统计
    fill_white_count = 0
    fill_surround_count = 0
    fill_dark_count = 0
    
    # 记录哪些位置是因为黑色被填充的（用于调试图）
    dark_fill_mask = np.zeros((h, w), dtype=np.uint8)
    
    for y, x in zip(ys, xs):
        # 计算采样窗口边界
        y_min = max(0, y - surround_radius)
        y_max = min(h, y + surround_radius + 1)
        x_min = max(0, x - surround_radius)
        x_max = min(w, x + surround_radius + 1)
        
        # 提取周围区域
        surround_patch = img[y_min:y_max, x_min:x_max]
        surround_mask_patch = final_mask[y_min:y_max, x_min:x_max]
        
        # 只取非水印区域的像素作为背景参考
        valid_pixels = surround_patch[surround_mask_patch == 0]
        
        if valid_pixels.size == 0:
            # 如果周围全是水印，默认填白色
            result[y, x] = [255, 255, 255]
            fill_white_count += 1
            continue
            
        # 判断周围是否有超过一半是接近黑色的
        if dark_surround_fill_white:
            is_dark_max = np.all(valid_pixels <= dark_threshold_max, axis=1)
            is_dark_min = np.all(valid_pixels >= dark_threshold_min, axis=1)
            is_dark = is_dark_max & is_dark_min
            dark_ratio = np.sum(is_dark) / len(is_dark)
            if dark_ratio > 0.5:
                result[y, x] = [255, 255, 255]
                fill_dark_count += 1
                dark_fill_mask[y, x] = 255
                continue
        
        # 判断周围是否有超过一半是接近白色的
        is_white = np.all(valid_pixels > white_threshold, axis=1)
        white_ratio = np.sum(is_white) / len(is_white)
        
        if white_ratio > 0.5:
            # 周围主要是白色，填充白色
            result[y, x] = [255, 255, 255]
            fill_white_count += 1
        else:
            # 否则，找周围出现最多的颜色
            quantized_patch = quantized_img[y_min:y_max, x_min:x_max]
            valid_quantized = quantized_patch[surround_mask_patch == 0]
            
            if valid_quantized.size == 0:
                result[y, x] = [255, 255, 255]
                fill_white_count += 1
                continue
                
            # 将颜色转为元组以便统计
            colors = [tuple(c) for c in valid_quantized]
            most_common_color = Counter(colors).most_common(1)[0][0]
            
            # 用原始图像中该颜色组的平均值填充（更平滑）
            color_mask = np.all(valid_quantized == most_common_color, axis=1)
            avg_color = np.mean(valid_pixels[color_mask], axis=0).astype(np.uint8)
            
            result[y, x] = avg_color
            fill_surround_count += 1
            
    print(f"[INFO] 智能填充统计: 填充白色={fill_white_count}, 填充周围色={fill_surround_count}, 因四周黑色填充白色={fill_dark_count}")
    return result, dark_fill_mask


def remove_gray_watermark(
    input_path,
    output_path,
    watermark_area_img=None,
    gray_range=(130, 220),
    lower_val=160,
    upper_val=230,
    dilate_size=3,
    smart_fill=True,
    surround_radius=5,
    white_threshold=200,
    dark_threshold_min=0, 
    dark_threshold_max = 150,
    dark_surround_fill_white=True,
    debug=False,
):
    """
    检测并填充灰色水印。
    """
    # 读取输入图片
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"无法读取输入图片: {input_path}")
    
    h, w = img.shape[:2]
    
    # 初始化 area_mask
    area_mask = None
    
    # 处理水印区域图片
    if watermark_area_img is not None:
        area_img = cv2.imread(watermark_area_img, cv2.IMREAD_UNCHANGED)
        
        if area_img is None:
            print(f"[WARN] 无法读取水印区域图片: {watermark_area_img}，将整图作为水印区域")
            area_mask = np.ones((h, w), dtype=np.uint8) * 255
        elif area_img.shape[-1] == 4:
            # 提取 alpha 通道
            alpha = area_img[:, :, 3]
            area_mask_raw = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)[1]
            # 【关键修复】缩放到输入图片尺寸
            area_mask = cv2.resize(area_mask_raw, (w, h))
            print(f"[INFO] 水印区域图片已加载，原始尺寸: {area_img.shape[:2]}, 缩放至: ({h}, {w})")
        else:
            print(f"[WARN] 水印区域图片没有 alpha 通道（通道数: {area_img.shape[-1]}），将整图作为水印区域")
            area_mask = np.ones((h, w), dtype=np.uint8) * 255
    else:
        # 没有传水印区域图片，整图都算水印区域
        area_mask = np.ones((h, w), dtype=np.uint8) * 255
    
    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 灰度范围检测
    gray_range_mask = cv2.inRange(gray, gray_range[0], gray_range[1])
    
    # 灰度检测与区域限制的交集
    combined = cv2.bitwise_and(gray_range_mask, area_mask)
    
    # 膨胀
    kernel = np.ones((dilate_size, dilate_size), np.uint8)
    mask = cv2.dilate(combined, kernel, iterations=1)
    
    # RGB 范围检测
    range_mask = cv2.inRange(
        img,
        (lower_val, lower_val, lower_val),
        (upper_val, upper_val, upper_val),
    )
    
    # 最终掩码 = 膨胀掩码 & RGB范围
    final_mask = cv2.bitwise_and(mask, range_mask)
    
    # 填充
    if smart_fill:
        result, dark_fill_mask = smart_fill_watermark(
            img, final_mask, surround_radius, white_threshold, 
            dark_threshold_min, 
            dark_threshold_max,
            dark_surround_fill_white,
        )
    else:
        result = img.copy()
        result[final_mask > 0] = [255, 255, 255]
        dark_fill_mask = np.zeros((h, w), dtype=np.uint8)
    
    # 保存结果
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, result)
    
    # 调试模式：保存中间图片
    if debug:
        debug_dir = os.path.join(
            os.path.dirname(output_path) or ".",
            os.path.basename(output_path).split(".")[0] + "_debug",
        )
        os.makedirs(debug_dir, exist_ok=True)
        
        # 安全获取 alpha 和 area_mask_raw
        alpha_debug = np.zeros((h, w), dtype=np.uint8)
        area_mask_raw_debug = np.zeros((h, w), dtype=np.uint8)
        area_img_bgr_debug = np.zeros((h, w, 3), dtype=np.uint8)
        
        if watermark_area_img is not None:
            area_img_check = cv2.imread(watermark_area_img, cv2.IMREAD_UNCHANGED)
            if area_img_check is not None and area_img_check.shape[-1] == 4:
                alpha_debug = area_img_check[:, :, 3]
                area_mask_raw_debug = cv2.threshold(alpha_debug, 1, 255, cv2.THRESH_BINARY)[1]
                area_img_bgr_debug = area_img_check[:, :, :3]
        
        debug_files = [
            ("01_原图.jpg", img),
            ("02_灰度图.jpg", gray),
            ("03_alpha通道.png", alpha_debug),
            ("04_area_mask_原始.png", area_mask_raw_debug),
            ("05_area_mask_已缩放至输入图尺寸.png", area_mask),
            ("06_area图片_BGR.jpg", area_img_bgr_debug),
            ("07_灰度范围检测.png", gray_range_mask),
            ("08_灰度检测与区域交集.png", combined),
            ("09_膨胀后掩码.png", mask),
            ("10_RGB范围检测.png", range_mask),
            ("11_最终掩码.png", final_mask),
            ("12_白色填充结果.jpg", result),
        ]
        
        # 如果开启了智能填充，保存智能填充类型图
        if smart_fill:
            # 黑色=因黑色填充白色，灰色=填充周围色，白色=因白色填充白色
            fill_type_img = np.zeros((h, w), dtype=np.uint8)
            fill_type_img[final_mask > 0] = 128  # 默认填充周围色
            fill_type_img[dark_fill_mask > 0] = 0  # 因黑色填充白色
            # 因白色填充白色的可以通过排除法得到（这里简化处理，主要看黑色和周围色）
            debug_files.append(("13_智能填充类型图.png", fill_type_img))
        
        for filename, data in debug_files:
            path = os.path.join(debug_dir, filename)
            cv2.imwrite(path, data)
        
        # 打印调试总结
        print("\n" + "=" * 50)
        print("【调试总结】")
        print(f"  area_mask 非零像素: {cv2.countNonZero(area_mask)}")
        print(f"  gray_range_mask 非零像素: {cv2.countNonZero(gray_range_mask)}")
        print(f"  combined 非零像素: {cv2.countNonZero(combined)}")
        print(f"  mask 非零像素: {cv2.countNonZero(mask)}")
        print(f"  range_mask 非零像素: {cv2.countNonZero(range_mask)}")
        print(f"  final_mask 非零像素: {cv2.countNonZero(final_mask)}")
        print(f"  调试图片保存至: {debug_dir}")
        print("=" * 50 + "\n")
        
        if cv2.countNonZero(final_mask) == 0:
            print("[WARN] final_mask 全为零，不会填充任何像素！")
    
    return result


if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/20260830/0902钢板去水印/333"


    watermark_area_img = None

    # dark_threshold
    # 20 ~ 40（极暗/纯黑）：只识别接近纯黑的颜色。如果你的背景是深灰、深蓝或深红，它们不会被判定为黑色。
    # 50（默认推荐）：能识别大部分常见的黑色和非常深的灰色。
    # 60 ~ 80（深灰/暗色）：如果你的背景是深灰色、暗色木纹等，建议设置在这个范围。
    # 100+（中灰偏暗）：不建议设置这么高，否则普通的阴影或中等深度的颜色都会被误判为黑色，导致大面积被强制填充为白色。

    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_智能填充22{ext}"

        remove_gray_watermark(
            input_path=input_path,
            output_path=output_path,
            watermark_area_img=watermark_area_img,
            gray_range=(130, 220),
            lower_val=160,
            upper_val=230,
            dilate_size=3,
            smart_fill=True,
            surround_radius=5,
            white_threshold=200,
            dark_threshold_min=0, 
            dark_threshold_max = 150,            # 小于50算接近黑色
            dark_surround_fill_white=True,  # 开启四周黑色强制填白
            debug=False,
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            remove_gray_watermark(
                input_path=input_file,
                output_path=output_file,
                watermark_area_img=watermark_area_img,
                gray_range=(130, 220),
                lower_val=160,
                upper_val=230,
                dilate_size=3,
                smart_fill=True,
                surround_radius=5,
                white_threshold=200,
                dark_threshold_min=0, 
                dark_threshold_max = 150,            # 小于50算接近黑色
                dark_surround_fill_white=True,  # 开启四周黑色强制填白
                debug=False,
            )

        output_dir = f"{input_path}_output_智能去水印"
        batch_process_file_with_callback(
            input_dir=input_path,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"路径错误: {input_path}")


