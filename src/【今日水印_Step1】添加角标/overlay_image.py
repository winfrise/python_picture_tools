import os
from PIL import Image
from typing import List, Dict, Optional


def _resolve_position(pos_x: int, pos_y: int, 
                      canvas_w: int, canvas_h: int, 
                      patch_w: int, patch_h: int) -> tuple:
    """
    解析位置坐标。
    x 正数从左边开始，负数从右边开始
    y 正数从上边开始，负数从下边开始
    返回 patch 左上角坐标 (x, y)
    """
    # 计算 x
    if pos_x >= 0:
        real_x = pos_x
    else:
        real_x = canvas_w + pos_x - patch_w  # 负数：从右往左偏移

    # 计算 y
    if pos_y >= 0:
        real_y = pos_y
    else:
        real_y = canvas_h + pos_y - patch_h

    return real_x, real_y


def _resize_input_image(input_image: Image.Image,
                        base_size: Optional[tuple]) -> Image.Image:
    """将输入图片调整到基准尺寸（宽, 高）。base_size 为 None 时不调整。"""
    if base_size is None:
        return input_image
    base_w, base_h = base_size
    if input_image.size == (base_w, base_h):
        return input_image
    return input_image.resize((base_w, base_h), Image.LANCZOS)


def _paste_patches(canvas: Image.Image,
                   patches: List[Dict]) -> Image.Image:
    """
    在画布上叠加多个 patch。
    patches 每个元素: {"path": 图片路径 或 Image对象, "x": int, "y": int}
    """
    canvas_w, canvas_h = canvas.size

    for item in patches:
        patch = item["path"]
        pos_x = int(item.get("x", 0))
        pos_y = int(item.get("y", 0))

        # 支持传入 PIL.Image 对象或文件路径
        if isinstance(patch, Image.Image):
            patch_img = patch
        else:
            if not os.path.exists(patch):
                raise FileNotFoundError(f"图片不存在: {patch}")
            patch_img = Image.open(patch)

        # 如果有配置 patch 的缩放尺寸（可选）
        if "width" in item and "height" in item:
            patch_img = patch_img.resize(
                (int(item["width"]), int(item["height"])), Image.LANCZOS
            )

        # 如果是带透明通道的 png，用自身作为 mask
        if patch_img.mode in ("RGBA", "LA") or (
            patch_img.mode == "P" and "transparency" in patch_img.info
        ):
            patch_img = patch_img.convert("RGBA")
            mask = patch_img.split()[-1]
        else:
            patch_img = patch_img.convert("RGB")
            mask = None

        # 计算实际位置
        real_x, real_y = _resolve_position(
            pos_x, pos_y, canvas_w, canvas_h,
            patch_img.width, patch_img.height
        )

        # 若画布为 RGB 而 patch 为 RGBA，需要先转 RGBA 画布
        if mask is not None and canvas.mode != "RGBA":
            canvas = canvas.convert("RGBA")

        canvas.paste(patch_img, (real_x, real_y), mask)

        if isinstance(item["path"], str):
            patch_img.close()

    return canvas


def add_images_to_single(input_image: str,
                         output_image: str,
                         image_list: List[Dict],
                         base_size: Optional[tuple] = (2304, 4096)) -> str:
    """
    给单张图片添加多个子图片。

    :param input_image: 输入图片路径
    :param output_image: 输出图片路径
    :param image_list: 子图片配置列表，每个元素形如:
                       {"path": "patch.png", "x": 100, "y": 100}
                       可选: {"width": 200, "height": 100} 指定 patch 的显示尺寸
    :param base_size: 基准尺寸 (width, height)，默认 (2304, 4096)。
                      设置为 None 时不调整输入图片尺寸。
                      也可以只指定高: 传入 (None, 4096) 则按比例缩放宽度。
    :return: 输出图片路径
    """
    if not os.path.exists(input_image):
        raise FileNotFoundError(f"输入图片不存在: {input_image}")

    img = Image.open(input_image)

    # 处理"只给宽或只给高"的情况：按比例缩放
    if base_size is not None:
        base_w, base_h = base_size
        if base_w is None and base_h is not None:
            ratio = base_h / img.height
            base_size = (int(img.width * ratio), base_h)
        elif base_h is None and base_w is not None:
            ratio = base_w / img.width
            base_size = (base_w, int(img.height * ratio))

    img = _resize_input_image(img, base_size)
    img = _paste_patches(img, image_list)

    # 输出目录不存在则创建
    out_dir = os.path.dirname(output_image)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # 依据扩展名保存
    ext = os.path.splitext(output_image)[1].lower()
    if ext in (".jpg", ".jpeg"):
        img = img.convert("RGB")
        img.save(output_image, quality=95)
    else:
        img.save(output_image)

    img.close()
    return output_image


def add_images_to_batch(input_dir: str,
                        output_dir: str,
                        image_list: List[Dict],
                        base_size: Optional[tuple] = (2304, 4096),
                        exts: tuple = (".jpg", ".jpeg", ".png", ".bmp", ".webp")) -> List[str]:
    """
    批量给目录下所有图片添加子图片。

    :param input_dir: 输入图片目录
    :param output_dir: 输出图片目录
    :param image_list: 子图片配置列表（同单张函数）
    :param base_size: 基准尺寸 (width, height) 或 None
    :param exts: 需要处理的图片扩展名
    :return: 成功输出的文件路径列表
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"输入目录不存在: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)
    results = []

    for name in sorted(os.listdir(input_dir)):
        if not name.lower().endswith(exts):
            continue
        src = os.path.join(input_dir, name)
        dst = os.path.join(output_dir, name)
        try:
            add_images_to_single(src, dst, image_list, base_size=base_size)
            results.append(dst)
            print(f"[OK] {src} -> {dst}")
        except Exception as e:
            print(f"[FAIL] {src}: {e}")

    return results