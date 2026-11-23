# image_resizer.py
from PIL import Image
import os
from pathlib import Path


# ============================================================
# 一、核心纯函数（可被任意地方复用）
# ============================================================

def _resolve_target_size(orig_w, orig_h, target_w, target_h):
    """只给宽/只给高时，按原图比例补全另一个；都不给则保持原尺寸。"""
    if target_w and not target_h:
        target_h = round(target_w * orig_h / orig_w)
    elif target_h and not target_w:
        target_w = round(target_h * orig_w / orig_h)
    elif not target_w and not target_h:
        target_w, target_h = orig_w, orig_h
    return target_w, target_h


def _prepare_mode_for_save(img, output_path):
    """根据输出格式修正图像模式（JPEG 不支持 RGBA/P）。"""
    ext = Path(output_path).suffix.lower()
    if ext in (".jpg", ".jpeg"):
        if img.mode in ("RGBA", "LA", "P"):
            # 用白色背景合成，避免透明区域变黑
            if img.mode == "P":
                img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            return bg
        if img.mode != "RGB":
            return img.convert("RGB")
    return img


def _save_image(img, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    ext = Path(output_path).suffix.lower()
    img = _prepare_mode_for_save(img, output_path)

    if ext in (".jpg", ".jpeg"):
        img.save(output_path, quality=95, subsampling=0, optimize=True)
    elif ext == ".png":
        img.save(output_path, optimize=True)
    else:
        img.save(output_path)


def resize_one(input_path, output_path, target_size_func):
    """
    处理单张图片：按 target_size_func 计算目标尺寸，等比缩放后裁剪/填充到目标尺寸。

    :param target_size_func: (orig_w, orig_h) -> (target_w, target_h)
                             只返回一个值时另一个传 None，会自动按比例补全。
    :return: 最终图像尺寸 (w, h)
    """
    input_path, output_path = str(input_path), str(output_path)
    img = Image.open(input_path)
    orig_w, orig_h = img.size

    target_w, target_h = target_size_func(orig_w, orig_h)
    target_w, target_h = _resolve_target_size(orig_w, orig_h, target_w, target_h)

    # 已符合目标尺寸，直接保存
    if (orig_w, orig_h) == (target_w, target_h):
        _save_image(img, output_path)
        print(f"[跳过缩放] {output_path} | {orig_w}x{orig_h}")
        return img.size


    scale = target_w / orig_w

    scaled_w = round(orig_w * scale)
    scaled_h = round(orig_h * scale)

    img = img.resize((scaled_w, scaled_h), Image.LANCZOS)

    # 裁剪 / 填充到目标尺寸
    cur_w, cur_h = img.size
    if cur_w > target_w or cur_h > target_h:
        # 水平居中、垂直靠顶部裁剪
        left = max(0, (cur_w - target_w) // 2)
        top = 0
        img = img.crop((left, top, left + target_w, top + target_h))
    elif cur_w < target_w or cur_h < target_h:
        # 白色画布，水平居中、贴顶部
        has_alpha = img.mode in ("RGBA", "LA", "P")
        canvas = Image.new(
            "RGBA" if has_alpha else "RGB",
            (target_w, target_h),
            (255, 255, 255, 255) if has_alpha else (255, 255, 255),
        )
        if has_alpha and img.mode != "RGBA":
            img = img.convert("RGBA")
        paste_x = (target_w - cur_w) // 2
        canvas.paste(img, (paste_x, 0), img if has_alpha else None)
        img = canvas

    _save_image(img, output_path)
    print(f"[完成] {output_path} | {orig_w}x{orig_h} -> {img.size[0]}x{img.size[1]}")
    return img.size


# ============================================================
# 二、对外暴露的两个方法
# ============================================================

def process_single_image(input_path, target_size_func, output_path=None, suffix="_output"):
    """单文件处理。output_path 不传则自动生成：原文件名 + suffix。"""
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"不是有效文件: {input_path}")

    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}{suffix}{input_path.suffix}")
    return resize_one(input_path, output_path, target_size_func)


def process_batch_images(input_dir, target_size_func, output_dir=None,
                         extensions=(".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"),
                         callback_func=None):
    """
    批量处理目录下所有图片（递归）。
    :return: [(输出文件路径, 最终尺寸), ...]
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"不是有效目录: {input_dir}")

    output_dir = Path(output_dir) if output_dir else input_dir.with_name(f"{input_dir.name}_output_改尺寸")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    files = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() 
        and p.suffix.lower() in extensions
        and not p.name.startswith("._")  # 👈 加上这个过滤条件
    )

    for f in files:
        rel = f.relative_to(input_dir)
        out_path = output_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            size = resize_one(f, out_path, target_size_func)
            results.append((str(out_path), size))
            if callback_func:
                callback_func(str(f), str(out_path))
        except Exception as e:
            print(f"[失败] {f} -> {e}")

    print(f"\n批量处理完成: 共 {len(results)}/{len(files)} 张成功，输出目录: {output_dir}")
    return results