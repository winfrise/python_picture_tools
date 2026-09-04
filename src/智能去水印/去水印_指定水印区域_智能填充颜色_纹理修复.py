import cv2
import numpy as np
import os
import time


def smart_fill_watermark(img, mask, surround_radius=5, white_threshold=200):
    """
    智能填充水印区域：
    - 如果水印周围（surround_radius范围内）接近白色（所有通道 > white_threshold），则填充白色
    - 否则，填充周围出现最多的颜色

    Args:
        img: 原始BGR图像 (H, W, 3)
        mask: 水印掩码，>0 的像素是需要填充的区域
        surround_radius: 向外采样扩展的半径（像素）
        white_threshold: 所有通道都大于此值则认为是"近白色"
    """
    result = img.copy()
    h, w = img.shape[:2]
    mask_bool = mask > 0

    # 获取需要填充的像素坐标
    ys, xs = np.where(mask_bool)
    if len(ys) == 0:
        return result, 0, 0

    # 预计算周围采样区域
    # 用膨胀来快速得到"水印区域+周围一圈"
    kernel = np.ones((surround_radius * 2 + 1, surround_radius * 2 + 1), np.uint8)
    dilated_mask = cv2.dilate(mask.astype(np.uint8), kernel, iterations=1)
    dilated_bool = dilated_mask > 0

    # 统计填充类型（用于调试）
    fill_white_count = 0
    fill_surround_count = 0

    # 颜色量化参数（每32一个档位，减少颜色数量使统计更稳定）
    quantize_div = 32

    for y, x in zip(ys, xs):
        # 采样窗口：[y-r, y+r+1], [x-r, x+r+1]
        y1 = max(0, y - surround_radius)
        y2 = min(h, y + surround_radius + 1)
        x1 = max(0, x - surround_radius)
        x2 = min(w, x + surround_radius + 1)

        # 取窗口内非水印区域（即 dilated_mask 中但 mask 外）的像素
        surround_region = img[y1:y2, x1:x2]
        surround_mask = dilated_bool[y1:y2, x1:x2] & ~mask_bool[y1:y2, x1:x2]

        surround_pixels = surround_region[surround_mask]

        if len(surround_pixels) == 0:
            # 没有周围像素可采样，直接填充白色
            result[y, x] = [255, 255, 255]
            fill_white_count += 1
            continue

        # 判断周围像素是否接近白色
        # 统计所有通道都 > white_threshold 的像素比例
        all_white = np.all(surround_pixels > white_threshold, axis=1)
        white_ratio = np.sum(all_white) / len(surround_pixels)

        if white_ratio > 0.5:
            # 超过50%是近白色，填充白色
            result[y, x] = [255, 255, 255]
            fill_white_count += 1
        else:
            # 找周围出现最多的颜色（量化后统计）
            quantized = (surround_pixels // quantize_div) * quantize_div + quantize_div // 2
            # 限制在 0~255 范围内
            quantized = np.clip(quantized, 0, 255).astype(np.uint8)

            # 将3通道量化值合并为单个整数以便统计
            # 每个通道用 0~7 (256/32=8个档位)
            r_quant = quantized[:, 0] // quantize_div
            g_quant = quantized[:, 1] // quantize_div
            b_quant = quantized[:, 2] // quantize_div
            combined = r_quant * 64 + g_quant * 8 + b_quant

            # 找出现最多的颜色
            unique, counts = np.unique(combined, return_counts=True)
            most_common_idx = np.argmax(counts)
            most_common = unique[most_common_idx]

            # 还原为RGB值
            fill_color = np.array(
                [(most_common // 64) * quantize_div + quantize_div // 2,
                 (most_common % 64 // 8) * quantize_div + quantize_div // 2,
                 (most_common % 8) * quantize_div + quantize_div // 2],
                dtype=np.uint8
            )
            fill_color = np.clip(fill_color, 0, 255)
            result[y, x] = fill_color.tolist()
            fill_surround_count += 1

    return result, fill_white_count, fill_surround_count

def advanced_fill_and_inpaint(img, mask, inpaint_radius=3, algo=cv2.INPAINT_TELEA):
    """
    高级填充策略：先颜色填充，再纹理修复
    :param img: 原始图像 (BGR)
    :param mask: 水印掩码 (单通道，白色为水印区域)
    :param inpaint_radius: Inpaint算法的修复半径，越大平滑度越高，但可能模糊细节
    :param algo: 修复算法，推荐 cv2.INPAINT_TELEA (基于快速行进法) 或 cv2.INPAINT_NS (基于流体动力学)
    """
    
    # --- 第一步：执行你原本的智能颜色填充 ---
    # 这一步负责把大面积的颜色填好，解决“底色不对”的问题
    # 注意：这里调用的是你之前写好的那个 smart_fill 函数
    filled_img = smart_fill_watermark(img, mask) 
    
    # --- 第二步：执行 OpenCV 的 Inpaint 修复 ---
    # 此时 filled_img 中虽然颜色对了，但边缘可能很硬。
    # 我们再次把 mask 传入 inpaint，让它基于 filled_img 进行边缘柔化和纹理重建。
    # 关键点：inpaint 会参考 mask 边缘外围的像素来“画”进 mask 内部
    final_result = cv2.inpaint(filled_img, mask, inpaintRadius=inpaint_radius, flags=algo)
    
    return final_result


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
    debug=False,
):
    """
    检测并填充灰色水印为白色（或智能填充周围颜色）。

    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        watermark_area_img: 水印区域图片路径（PNG透明图，非透明区域为水印区域）
        gray_range: 灰度值范围 (min, max)
        lower_val: RGB 下限
        upper_val: RGB 上限
        dilate_size: 膨胀核大小
        smart_fill: 是否启用智能填充（True=智能填充，False=统一白色填充）
        surround_radius: 智能填充时，向外扩展多少像素来采样周围颜色
        white_threshold: 所有通道都大于此值则认为是"近白色"
        debug: 是否保存中间调试图片
    """

    start_time = time.time()

    print(f"正在处理图片:{input_path}")

    # 读取输入图片
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"无法读取输入图片: {input_path}")

    h, w = img.shape[:2]

    # 初始化 area_mask
    area_mask = None
    area_img = None
    alpha = None
    area_mask_raw = None

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

    # 填充处理
    if smart_fill:
        result, fill_white_count, fill_surround_count = smart_fill_watermark(
            img, final_mask, surround_radius=surround_radius, white_threshold=white_threshold
        )
    else:
        result = img.copy()
        result[final_mask > 0] = [255, 255, 255]
        fill_white_count = cv2.countNonZero(final_mask)
        fill_surround_count = 0



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
            ("12_智能填充结果.jpg", result),
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
        print(f"  智能填充模式: {'启用' if smart_fill else '禁用'}")
        print(f"  填充为白色的像素数: {fill_white_count}")
        print(f"  填充为周围色的像素数: {fill_surround_count}")
        print(f"  调试图片保存至: {debug_dir}")
        print("=" * 50 + "\n")

        if cv2.countNonZero(final_mask) == 0:
            print("[WARN] final_mask 全为零，不会填充任何像素！")
            print("  可能原因:")
            print("  1. area_mask 全为零 -> 检查水印区域图片的 alpha 通道")
            print("  2. gray_range_mask 全为零 -> 调整 gray_range 参数")
            print("  3. range_mask 全为零 -> 调整 lower_val/upper_val 参数")
            print("  4. combined 和 range_mask 无交集 -> 检查参数是否匹配实际水印颜色")


    # 保存结果
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, result)

    print(f"处理完成，保存至:{output_path}")

    end_time = time.time()
    print(f"运行耗时: {end_time - start_time:.4f} 秒")


    return result


if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/20260830/0902钢板去水印/test/001.jpg"

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
        smart_fill=True,
        surround_radius=5,
        white_threshold=200,
        debug=False,
    )