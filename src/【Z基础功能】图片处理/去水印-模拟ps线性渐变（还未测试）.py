#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去水印脚本 - 基于 Photoshop「线性减淡(加)」混合模式原理
优化版本：修复色偏、颜色匹配精度、膨胀范围可控、路径参数化等问题
"""

import cv2
import numpy as np
import os
import argparse
from pathlib import Path


def remove_watermark_with_exclusion(
    image_path: str,
    watermark_path: str,
    output_path: str,
    exclude_color_bgr: tuple = (0, 0, 0),
    exclude_threshold: int = 30,
    use_hsv_mask: bool = True,
    dilate_kernel_size: int = 5,
    dilate_iterations: int = 1,
    watermark_to_gray: bool = True,
) -> np.ndarray:
    """
    基于线性减淡原理去水印，并排除特定颜色的矩形区域。

    参数说明:
        image_path:         原图路径
        watermark_path:     水印图路径（建议白底透明/黑色水印）
        output_path:        输出文件路径
        exclude_color_bgr:  需要排除不去水的颜色（BGR格式），默认黑色 (0,0,0)
        exclude_threshold:  颜色匹配容差，默认 30
        use_hsv_mask:       是否使用 HSV 空间进行颜色匹配（推荐 True，对光照变化更鲁棒）
        dilate_kernel_size: 膨胀核大小，默认 5
        dilate_iterations:  膨胀次数，默认 1（减少误排除）
        watermark_to_gray:  是否将水印先转灰度再反色（避免彩色水印色偏，推荐 True）
    """
    # 1. 读取原图和水印图
    img = cv2.imread(image_path)
    wm = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)  # 保留 Alpha 通道

    if img is None:
        raise ValueError(f"无法读取原图: {image_path}")
    if wm is None:
        raise ValueError(f"无法读取水印图: {watermark_path}")

    # 确保水印图与原图尺寸一致
    if img.shape[:2] != wm.shape[:2]:
        wm = cv2.resize(wm, (img.shape[1], img.shape[0]))

    # 2. 水印处理：转灰度后反色（避免彩色水印导致的色偏）
    if len(wm.shape) == 3:
        wm_gray = cv2.cvtColor(wm, cv2.COLOR_BGR2GRAY)
    else:
        wm_gray = wm

    # 反色：水印越黑，反色后越亮
    inverted_wm_gray = 255 - wm_gray

    # 转回 3 通道以匹配原图 BGR
    inverted_wm = cv2.cvtColor(inverted_wm_gray, cv2.COLOR_GRAY2BGR)

    # 3. 生成排除区域的掩码
    if use_hsv_mask:
        # HSV 空间颜色匹配，对光照/亮度变化更鲁棒
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 将 BGR 排除颜色转换为 HSV
        exclude_color_np = np.uint8([[list(exclude_color_bgr)]])
        exclude_color_hsv = cv2.cvtColor(exclude_color_np, cv2.COLOR_BGR2HSV)[0][0]

        # 在 HSV 空间构建范围（H 通道 wrap 处理）
        h, s, v = exclude_color_hsv

        # 色相范围（考虑 H 通道 0-179 的 wrap-around）
        h_lower = max(0, h - exclude_threshold)
        h_upper = min(179, h + exclude_threshold)

        # 饱和度/明度容差
        s_lower = max(0, s - exclude_threshold * 2)
        s_upper = min(255, s + exclude_threshold * 2)
        v_lower = max(0, v - exclude_threshold * 2)
        v_upper = min(255, v + exclude_threshold * 2)

        lower_bound_hsv = np.array([h_lower, s_lower, v_lower], dtype=np.uint8)
        upper_bound_hsv = np.array([h_upper, s_upper, v_upper], dtype=np.uint8)

        color_mask = cv2.inRange(img_hsv, lower_bound_hsv, upper_bound_hsv)
    else:
        # 回退到 BGR 空间匹配（兼容旧用法）
        lower_bound = np.array(
            [max(0, c - exclude_threshold) for c in exclude_color_bgr], dtype=np.uint8
        )
        upper_bound = np.array(
            [min(255, c + exclude_threshold) for c in exclude_color_bgr], dtype=np.uint8
        )
        color_mask = cv2.inRange(img, lower_bound, upper_bound)

    # 4. 形态学操作：膨胀连接碎片（次数可配置，避免过度扩大）
    kernel = np.ones((dilate_kernel_size, dilate_kernel_size), np.uint8)
    if dilate_iterations > 0:
        color_mask = cv2.dilate(color_mask, kernel, iterations=dilate_iterations)

    # 5. 执行「线性减淡」混合
    #    公式：结果 = 基色 + 混合色（cv2.add 自动做 saturate 裁剪）
    result = cv2.add(img, inverted_wm)

    # 6. 应用排除掩码：掩码为 255 的区域保留原图不变
    #    使用 astype(bool) 避免 uint8 比较的类型警告
    mask_3ch = color_mask[:, :, np.newaxis].astype(bool)
    final_result = np.where(mask_3ch, img, result)

    # 7. 保存结果
    cv2.imwrite(output_path, final_result)
    print(f"[OK] 处理完成: {output_path}")

    return final_result


# ==================== 批量处理函数 ====================

def batch_remove_watermark(
    input_dir: str,
    watermark_path: str,
    output_dir: str,
    exclude_color_bgr: tuple = (0, 0, 0),
    exclude_threshold: int = 30,
    use_hsv_mask: bool = True,
    dilate_kernel_size: int = 5,
    dilate_iterations: int = 1,
    watermark_to_gray: bool = True,
    supported_exts: tuple = (".png", ".jpg", ".jpeg", ".bmp", ".tif"),
):
    """
    批量对目录中的图片去水印。

    参数:
        input_dir:          输入图片目录
        watermark_path:     水印图路径
        output_dir:         输出目录（自动创建）
        exclude_color_bgr:  排除颜色 (BGR)
        exclude_threshold:  颜色容差
        use_hsv_mask:       使用 HSV 颜色匹配
        dilate_kernel_size: 膨胀核大小
        dilate_iterations:  膨胀次数
        watermark_to_gray:  水印转灰度
        supported_exts:     支持的文件扩展名
    """
    os.makedirs(output_dir, exist_ok=True)

    input_path = Path(input_dir)
    processed = 0
    failed = 0

    for file_path in input_path.iterdir():
        if file_path.suffix.lower() not in supported_exts:
            continue

        output_file = output_dir / file_path.name
        try:
            remove_watermark_with_exclusion(
                image_path=str(file_path),
                watermark_path=watermark_path,
                output_path=str(output_file),
                exclude_color_bgr=exclude_color_bgr,
                exclude_threshold=exclude_threshold,
                use_hsv_mask=use_hsv_mask,
                dilate_kernel_size=dilate_kernel_size,
                dilate_iterations=dilate_iterations,
                watermark_to_gray=watermark_to_gray,
            )
            processed += 1
        except Exception as e:
            print(f"[ERR] 处理失败 {file_path.name}: {e}")
            failed += 1

    print(f"\n批量处理完成: 成功 {processed} 张, 失败 {failed} 张")


# ==================== 命令行入口 ====================

def parse_args():
    parser = argparse.ArgumentParser(
        description="基于线性减淡原理去水印（优化版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单张图片
  python 去水印_优化版.py -i image.png -w mask.png -o output.png

  # 批量处理
  python 去水印_优化版.py -i ./images/ -w mask.png -o ./output/

  # 自定义排除颜色（红色 BGR=0,0,255）及参数
  python 去水印_优化版.py -i image.png -w mask.png -o output.png \\
      --exclude-color 0 0 255 --threshold 40 --dilate-iters 2
        """,
    )
    parser.add_argument("-i", "--input", required=True, help="输入图片路径或目录")
    parser.add_argument("-w", "--watermark", required=True, help="水印图路径")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径或目录")
    parser.add_argument(
        "--exclude-color",
        nargs=3,
        type=int,
        default=[0, 0, 0],
        metavar=("B", "G", "R"),
        help="排除不去水的颜色 BGR (默认: 0 0 0 黑色)",
    )
    parser.add_argument(
        "--threshold", type=int, default=30, help="颜色匹配容差 (默认: 30)"
    )
    parser.add_argument(
        "--no-hsv", action="store_true", help="禁用 HSV 匹配，回退到 BGR 空间"
    )
    parser.add_argument(
        "--dilate-kernel", type=int, default=5, help="膨胀核大小 (默认: 5)"
    )
    parser.add_argument(
        "--dilate-iters", type=int, default=1, help="膨胀次数 (默认: 1)"
    )
    parser.add_argument(
        "--no-gray-wm", action="store_true", help="不将水印转灰度（保留水印原始颜色）"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    exclude_color = tuple(args.exclude_color)
    use_hsv = not args.no_hsv
    wm_to_gray = not args.no_gray_wm

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file():
        # 单图模式
        remove_watermark_with_exclusion(
            image_path=str(input_path),
            watermark_path=args.watermark,
            output_path=str(output_path),
            exclude_color_bgr=exclude_color,
            exclude_threshold=args.threshold,
            use_hsv_mask=use_hsv,
            dilate_kernel_size=args.dilate_kernel,
            dilate_iterations=args.dilate_iters,
            watermark_to_gray=wm_to_gray,
        )
    elif input_path.is_dir():
        # 批量模式
        batch_remove_watermark(
            input_dir=str(input_path),
            watermark_path=args.watermark,
            output_dir=str(output_path),
            exclude_color_bgr=exclude_color,
            exclude_threshold=args.threshold,
            use_hsv_mask=use_hsv,
            dilate_kernel_size=args.dilate_kernel,
            dilate_iterations=args.dilate_iters,
            watermark_to_gray=wm_to_gray,
        )
    else:
        print(f"错误: 输入路径无效 -> {args.input}")