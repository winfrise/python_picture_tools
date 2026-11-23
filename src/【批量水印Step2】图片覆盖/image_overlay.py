from PIL import Image
from typing import List, Callable, Union, Optional
import os
import sys
import re
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback


# ============================================================
# 1. 核心：单张图覆盖（只负责合成，不涉及路径编排）
# ============================================================
def overlay_images(
    image_path: str,
    overlay_image_path: Union[str, Callable[[str, tuple], Optional[str]]],
    save_path: Optional[str] = None,
) -> Optional[Image.Image]:
    """
    将覆盖图叠加到背景图上。

    :param image_path: 背景图片路径
    :param overlay_image_path: 覆盖图路径，或回调函数 (image_path, size) -> 覆盖图路径
                               回调返回 None 表示跳过该图
    :param save_path: 可选，保存路径；不传则只返回 Image 对象
    :return: 合并后的 Image 对象；跳过时返回 None
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"背景图片未找到: {image_path}")

    image = Image.open(image_path).convert("RGBA")

    # 解析覆盖图路径（支持回调动态决定）
    if callable(overlay_image_path):
        overlay_image_path = overlay_image_path(image_path, image.size)

    if not overlay_image_path:
        print(f"跳过: 未指定覆盖图 -> {image_path}")
        return None
    if not os.path.exists(overlay_image_path):
        print(f"跳过: 覆盖图未找到 -> {overlay_image_path}")
        return None

    overlay_image = Image.open(overlay_image_path).convert("RGBA")
    image.paste(overlay_image, (0, 0), overlay_image)

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        out = image.convert("RGB") if save_path.lower().endswith((".jpg", ".jpeg")) else image
        out.save(save_path, quality=100, subsampling=0)
        print(f"已保存: {save_path}")

    return image


# ============================================================
# 2. 单个文件处理
# ============================================================
def process_single(
    image_path: str,
    overlay_image_path: Union[str, Callable[[str, tuple], Optional[str]]],
    output_path: Optional[str] = None,
    suffix: str = "_output_图片覆盖",
) -> Optional[Image.Image]:
    """
    处理单个文件。

    :param image_path: 输入图片路径
    :param overlay_image_path: 覆盖图路径或回调
    :param output_path: 显式指定输出路径；不传则用 suffix 自动生成
    :param suffix: 自动生成输出文件名时用的后缀
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"文件不存在: {image_path}")

    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}{suffix}{ext}"

    return overlay_images(image_path, overlay_image_path, save_path=output_path)


# ============================================================
# 3. 批量处理目录
# ============================================================
def process_batch(
    input_dir: str,
    overlay_image_path: Union[str, Callable[[str, tuple], Optional[str]]],
    output_dir: Optional[str] = None,
    suffix: str = "_output_图片覆盖",
) -> str:
    """
    批量处理目录下的所有图片。

    :param input_dir: 输入目录
    :param overlay_image_path: 覆盖图路径或回调
    :param output_dir: 输出目录；不传则自动生成 "{input_dir}{suffix}"
    :return: 实际使用的输出目录
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"目录不存在: {input_dir}")

    if output_dir is None:
        output_dir = f"{input_dir}{suffix}"

    def callback_func(input_file: str, output_file: str):
        try:
            overlay_images(input_file, overlay_image_path, save_path=output_file)
        except Exception as e:
            print(f"处理失败: {input_file} -> {e}")

    batch_process_file_with_callback(
        input_dir=input_dir,
        output_dir=output_dir,
        callback_func=callback_func,
    )
    return output_dir

