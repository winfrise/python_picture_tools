import cv2
import numpy as np
import os


def remove_gray_watermark(
    input_path,
    output_path,
    watermark_area_img=None,
    gray_range=(130, 220),
    lower_val=160,
    upper_val=230,
    dilate_size=3,
    debug=False,
):
    """
    检测并填充灰色水印为白色。
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        watermark_area_img: 水印区域图片路径（PNG透明图，非透明区域为水印区域）
        gray_range: 灰度值范围 (min, max)
        lower_val: RGB 下限
        upper_val: RGB 上限
        dilate_size: 膨胀核大小
        debug: 是否保存中间调试图片
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
    
    # 填充白色
    result = img.copy()
    result[final_mask > 0] = [255, 255, 255]
    
    # 保存结果
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, result)
    
    # 调试模式：保存中间图片
    if debug:
        debug_dir = os.path.join(
            os.path.dirname(output_path) or ".",
            os.path.basename(output_path).replace(".", "_debug"),
        )
        os.makedirs(debug_dir, exist_ok=True)
        
        debug_files = [
            ("01_原图.jpg", img),
            ("02_灰度图.jpg", gray),
            ("03_alpha通道.png", alpha if watermark_area_img and area_img is not None and area_img.shape[-1] == 4 else np.zeros((h, w), dtype=np.uint8)),
            ("04_area_mask_原始.png", area_mask_raw if watermark_area_img and area_img is not None and area_img.shape[-1] == 4 else np.zeros((h, w), dtype=np.uint8)),
            ("05_area_mask_已缩放至输入图尺寸.png", area_mask),
            ("06_area图片_BGR.jpg", area_img[:, :, :3] if watermark_area_img and area_img is not None and area_img.shape[-1] >= 3 else np.zeros((h, w, 3), dtype=np.uint8)),
            ("07_灰度范围检测.png", gray_range_mask),
            ("08_灰度检测与区域交集.png", combined),
            ("09_膨胀后掩码.png", mask),
            ("10_RGB范围检测.png", range_mask),
            ("11_最终掩码.png", final_mask),
            ("12_白色填充结果.jpg", result),
        ]
        
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
            print("  可能原因:")
            print("  1. area_mask 全为零 → 检查水印区域图片的 alpha 通道")
            print("  2. gray_range_mask 全为零 → 调整 gray_range 参数")
            print("  3. range_mask 全为零 → 调整 lower_val/upper_val 参数")
            print("  4. combined 和 range_mask 无交集 → 检查参数是否匹配实际水印颜色")
    
    return result


if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/20260830/0902钢板去水印/test/test2.jpg"

    base_name, ext = os.path.splitext(input_path)
    output_path = f"{base_name}_output_智能填充22{ext}"

    watermark_area_img = None

    remove_gray_watermark(
        input_path=input_path,
        output_path=output_path,
        watermark_area_img=watermark_area_img,
        gray_range=(130, 220),
        lower_val=160,
        upper_val=230,
        dilate_size=3,
        debug=True,
    )