# draw_text_on_image_steps.py
"""
多文本分步式图片水印（支持文件夹批量处理、保持原图目录层级、自定义临时目录、保留 meta.json）：
"""
import os
import json
import shutil
import inspect
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from scope_utils.text_equal_height_render_utils import (
    build_segment_fonts,
    render_text_on_canvas,
    measure_text_block,
    resolve_font_path,
    load_base_font,
    safe_filename,
)


# ============================================================
# 配置合并
# ============================================================
_OVERRIDABLE_KEYS = (
    "font_path", "font_size", "text_color", "match_digit_height",
    "blur_radius", "offset_left", "offset_bottom",
)

_COMMON_DEFAULTS = {
    "font_path": "arial.ttf", "font_size": 40, "text_color": "black",
    "match_digit_height": True, "blur_radius": 0, "offset_left": 0, "offset_bottom": 0,
}

def _merge_config(common_config, item):
    merged = dict(_COMMON_DEFAULTS)
    merged.update(common_config or {})
    for k in _OVERRIDABLE_KEYS:
        if k in item:
            merged[k] = item[k]
    merged["text"] = item.get("text", "")
    return merged


# ============================================================
# 工具函数：智能解析文本
# ============================================================
def _resolve_text(text_or_callable, image_path):
    """解析文本内容，支持传入函数并自动判断是否传入 image_path。"""
    if not callable(text_or_callable):
        return str(text_or_callable)
        
    try:
        sig = inspect.signature(text_or_callable)
        params = [
            p for p in sig.parameters.values() 
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        if params or any(p.kind == p.VAR_POSITIONAL for p in sig.parameters.values()):
            result = text_or_callable(image_path)
        else:
            result = text_or_callable()
    except Exception as e:
        print(f"[warn] 执行文本函数失败 ({e})，回退到无参调用")
        result = text_or_callable()

    return str(result) if result is not None else ""


# ============================================================
# 阶段一：text → 文字图片，存临时文件夹
# ============================================================
def _render_one_text_image(text, cfg, work_dir, index):
    font_path          = cfg["font_path"]
    font_size          = cfg["font_size"]
    text_color         = cfg["text_color"]
    match_digit_height = cfg["match_digit_height"]

    resolved_font_path = resolve_font_path(font_path)
    if match_digit_height:
        segments, base_font, target_h = build_segment_fonts(text, resolved_font_path, font_size)
    else:
        base_font = load_base_font(resolved_font_path, font_size)
        segments = [(text, "other", base_font)]
        target_h = 0

    bw, top_min, bottom_max = measure_text_block(segments)
    if bw <= 0:
        raise ValueError(f"文字宽度为 0（text={text!r}），请检查文本内容/字体")

    SAFE_PAD = 50
    canvas_w = bw + SAFE_PAD * 2
    canvas_h = (bottom_max - top_min) + SAFE_PAD * 2

    text_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_img)

    first_seg_text = segments[0][0] if segments else ""
    first_b = segments[0][2].getbbox(first_seg_text, anchor="ls") if first_seg_text else (0, 0, 0, 0)
    
    start_x = SAFE_PAD - first_b[0]
    baseline_y = SAFE_PAD + abs(top_min) 

    render_text_on_canvas(
        text_img, draw, start_x, baseline_y,
        segments, text_color, target_h,
    )

    # 自动裁掉多余透明边距
    bbox = text_img.getbbox()
    if bbox:
        text_img = text_img.crop(bbox)
    else:
        raise ValueError(f"渲染后未获取到有效文字像素（text={text!r}）")
    
    real_w, real_h = text_img.size
    text_image_path = os.path.join(work_dir, f"text_{index:03d}.png")
    text_img.save(text_image_path)

    meta = {
        "index": index, "text": text, "text_image": text_image_path,
        "width": real_w, "height": real_h, "font_path": font_path,
        "font_size": font_size, "text_color": text_color,
        "match_digit_height": match_digit_height, "blur_radius": cfg["blur_radius"],
        "offset_left": int(cfg["offset_left"]), "offset_bottom": int(cfg["offset_bottom"]),
    }
    print(f"  └─ 文字图 #{index:03d} 已生成: ({real_w}x{real_h}) text={text!r}")
    return meta


def generate_text_images(image_path, common_config, text_items, work_dir):
    os.makedirs(work_dir, exist_ok=True)
    metas = []
    for i, item in enumerate(text_items):
        if not isinstance(item, dict):
            raise TypeError(f"text_items[{i}] 必须是 dict，实际为 {type(item)}")
        if "text" not in item:
            raise KeyError(f"text_items[{i}] 缺少 'text' 字段")

        text = _resolve_text(item["text"], image_path)
        
        if not text.strip():
            print(f"  └─ [warn] text_items[{i}] 文本为空，跳过")
            continue

        cfg = _merge_config(common_config, item)
        meta = _render_one_text_image(text, cfg, work_dir, len(metas))
        metas.append(meta)

    if not metas:
        raise ValueError("没有任何有效文本项可渲染")

    # 【核心】生成并保留 meta.json
    with open(os.path.join(work_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)

    return metas


# ============================================================
# 阶段二：把每张文字图贴到 image_path 对应位置
# ============================================================
def _paste_one_text(base, meta):
    text_layer = Image.open(meta["text_image"]).convert("RGBA")
    bw, bh = meta["width"], meta["height"]
    canvas_w, canvas_h = base.size

    block_x = meta["offset_left"]
    block_y = canvas_h - meta["offset_bottom"] - bh

    if block_x < 0 or block_y < 0 or block_x + bw > canvas_w or block_y + bh > canvas_h:
        print(f"  └─ [warn] 文字 #{meta['index']:03d} 可能超出画布")

    blur_radius = meta.get("blur_radius", 0) or 0
    if blur_radius > 0:
        pad = int(blur_radius * 6) + 2
        padded = Image.new("RGBA", (bw + 2 * pad, bh + 2 * pad), (0, 0, 0, 0))
        padded.alpha_composite(text_layer, (pad, pad))
        padded = padded.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        text_layer = padded.crop((pad, pad, pad + bw, pad + bh))

    result = base.copy()
    dst_x = max(block_x, 0)
    dst_y = max(block_y, 0)
    src_x = dst_x - block_x
    src_y = dst_y - block_y
    w = min(bw - src_x, canvas_w - dst_x)
    h = min(bh - src_y, canvas_h - dst_y)
    
    if w > 0 and h > 0:
        crop = text_layer.crop((src_x, src_y, src_x + w, src_y + h))
        result.alpha_composite(crop, (dst_x, dst_y))
        
    return result


def compose_text_images(image_path, metas, config, output_path):
    base = Image.open(image_path).convert("RGBA")
    result = base
    for meta in metas:
        result = _paste_one_text(result, meta)

    save_ext = os.path.splitext(output_path)[1].lower()
    if save_ext in (".jpg", ".jpeg"):
        result.convert("RGB").save(output_path, quality=95)
    else:
        result.save(output_path)

    return output_path


# ============================================================
# 单个文件处理逻辑
# ============================================================
def _process_single_image(input_path, output_path, common_config, text_items, temp_image_dir, keep_work_dir):
    """
    处理单张图片。
    temp_image_dir: 当前原图对应的专属临时文件夹
    """
    os.makedirs(temp_image_dir, exist_ok=True)
    
    try:
        # 生成文字图（存入 temp_image_dir，包含 meta.json）
        metas = generate_text_images(input_path, common_config, text_items, temp_image_dir)
        # 合成到输出
        compose_text_images(input_path, metas, {}, output_path)
    finally:
        if not keep_work_dir:
            # 处理完直接删掉当前图片专属的临时文件夹
            try:
                shutil.rmtree(temp_image_dir)
            except Exception:
                pass
        else:
            print(f"  └─ [keep] 临时文件夹保留: {temp_image_dir}")


# ============================================================
# 主流程（支持单文件 / 文件夹批量）
# ============================================================
def draw_texts_on_image(
    image_path,
    text_items,
    work_root,           
    common_config=None,
    output_dir=None,
    keep_work_dir=True,
):
    if common_config is None:
        common_config = {}

    work_root = os.path.abspath(work_root)
    os.makedirs(work_root, exist_ok=True)
    image_path = os.path.abspath(image_path)
    
    # ================= 单文件模式 =================
    if os.path.isfile(image_path):
        if os.path.basename(image_path).startswith("."):
            print(f"[跳过] 这是一个隐藏文件: {image_path}")
            return None

        if output_dir is None:
            output_dir = os.path.dirname(image_path)
        os.makedirs(output_dir, exist_ok=True)
        
        base_name, ext = os.path.splitext(os.path.basename(image_path))
        joined = "_".join(safe_filename(str(item.get("text", "")))[:10] for item in text_items)[:60]
        output_name = f"{base_name}_{joined}{ext}" if joined else f"{base_name}_out{ext}"
        output_path = os.path.join(output_dir, output_name)
        
        # 单文件时，直接在 work_root 下建一个同名文件夹存放临时图片和 json
        temp_image_dir = os.path.join(work_root, base_name)
        
        print(f"[单文件] 处理: {image_path}")
        _process_single_image(image_path, output_path, common_config, text_items, temp_image_dir, keep_work_dir)
        print(f"[完成] 保存至: {output_path}\n")
        return output_path

    # ================= 文件夹批量模式 =================
    elif os.path.isdir(image_path):
        if output_dir is None:
            raise ValueError("批量处理文件夹时，必须指定 output_dir 参数")
        
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        
        print(f"[批量] 扫描文件夹: {image_path}")
        
        tasks = []
        for p in Path(image_path).rglob("*"):
            if any(part.startswith(".") for part in p.relative_to(image_path).parts):
                continue
            if p.is_file() and p.suffix.lower() in exts:
                tasks.append(p)
                
        if not tasks:
            print(f"[批量] 未找到任何有效图片文件。")
            return []

        print(f"[批量] 共找到 {len(tasks)} 张图片，开始处理...")

        results = []
        for p in tasks:
            rel_path = p.relative_to(image_path)
            
            # 1. 输出目录：保持原有层级
            out_p = Path(output_dir) / rel_path
            os.makedirs(out_p.parent, exist_ok=True)

            # 2. 临时目录：同样保持原目录层级。直接用原图文件名（不带后缀）作为文件夹名，例如：/work_root/2026/08/11/
            temp_image_dir = Path(work_root) / rel_path.parent / rel_path.stem
            temp_image_dir = str(temp_image_dir)

            print(f"--> 正在处理: {rel_path}")
            try:
                _process_single_image(str(p), str(out_p), common_config, text_items, temp_image_dir, keep_work_dir)
                print(f"  └─ 保存至: {out_p}")
                results.append(str(out_p))
            except Exception as e:
                print(f"  └─ [error] 处理失败: {e}")
                import traceback
                traceback.print_exc()
            
            print("-" * 40)
            
        print(f"[批量] 全部处理完毕。成功: {len(results)}/{len(tasks)}\n")
        return results

    else:
        raise FileNotFoundError(f"路径不存在: {image_path}")


# ============================================================
# 单文本兼容包装
# ============================================================
def draw_text_on_image(image_path, text, work_root, output_dir=None, config=None, **kwargs):
    config = config or {}
    common = {k: v for k, v in config.items() if k not in ("offset_left", "offset_bottom", "output_path", "overwrite")}
    item = {
        "text": text,
        "offset_left": config.get("offset_left", 0),
        "offset_bottom": config.get("offset_bottom", 0)
    }
    return draw_texts_on_image(
        image_path=image_path,
        text_items=[item],
        work_root=work_root,
        common_config=common,
        output_dir=output_dir,
        **kwargs,
    )


# ============================================================
# 测试与示例
# ============================================================
if __name__ == "__main__":
    from plugins.get_font_path import get_font_path

    def extract_date_from_path(img_path):
        import re
        filename = os.path.basename(img_path)
        match = re.search(r'(\d{8})', filename)
        if match:
            date_str = match.group(1)
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return "未知日期"

    input_dir = "/Volumes/西数4T外置/百度网盘默认下载/test"
    output_dir = "/Volumes/西数4T外置/百度网盘默认下载/test_output"
    custom_work_root = "/Volumes/西数4T外置/百度网盘默认下载/temp_watermarks"

    common_config = {
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "text_color": "#000000",
        "match_digit_height": True,
        "blur_radius": 0.0,
    }

    text_items = [
        {
            "text": extract_date_from_path,
            "offset_left": 20,
            "offset_bottom": 20,
        }
    ]

    draw_texts_on_image(
        image_path=input_dir,
        text_items=text_items,
        work_root=custom_work_root,
        common_config=common_config,
        output_dir=output_dir,
        keep_work_dir=True, 
    )