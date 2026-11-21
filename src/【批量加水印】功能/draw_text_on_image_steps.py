# draw_text_on_image_steps.py
"""
多文本分步式图片水印（支持从图片地址动态获取文本）：

  阶段一 generate_text_images()
      对每个文本项渲染成一张透明底文字图 → 存临时文件夹
      （text_000.png / text_001.png / ... + meta.json）

  阶段二 compose_text_images()
      读取每张文字图，按各自的 offset_left/offset_bottom 贴到 image_path → 保存
"""
import os
import json
import shutil
import uuid
import inspect

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
    "font_path",
    "font_size",
    "text_color",
    "match_digit_height",
    "blur_radius",
    "offset_left",
    "offset_bottom",
)

_COMMON_DEFAULTS = {
    "font_path": "arial.ttf",
    "font_size": 40,
    "text_color": "black",
    "match_digit_height": True,
    "blur_radius": 0,
    "offset_left": 0,
    "offset_bottom": 0,
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
    """
    解析文本内容：
    - 如果是字符串，直接返回。
    - 如果是函数，根据函数签名决定是否传入 image_path：
        - 如果函数接收至少 1 个参数，调用 text(image_path)
        - 如果不接收参数，调用 text()
    """
    if not callable(text_or_callable):
        return str(text_or_callable)
        
    try:
        # 检查函数签名，看能否接收参数
        sig = inspect.signature(text_or_callable)
        # 过滤掉 *args, **kwargs 的情况，如果有正常的 positional 参数
        params = [
            p for p in sig.parameters.values() 
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        if params or any(p.kind == p.VAR_POSITIONAL for p in sig.parameters.values()):
            # 函数能接收参数，传入 image_path
            result = text_or_callable(image_path)
        else:
            # 无参函数，直接调用
            result = text_or_callable()
    except Exception as e:
        print(f"[warn] 执行文本函数失败 ({e})，回退到无参调用")
        result = text_or_callable()

    return str(result) if result is not None else ""


# ============================================================
# 阶段一：text → 文字图片（每个文本一张），存临时文件夹
# ============================================================

def _render_one_text_image(text, cfg, work_dir, index):
    font_path          = cfg["font_path"]
    font_size          = cfg["font_size"]
    text_color         = cfg["text_color"]
    match_digit_height = cfg["match_digit_height"]

    # 1. 构建分段字体
    resolved_font_path = resolve_font_path(font_path)
    if match_digit_height:
        segments, base_font, target_h = build_segment_fonts(text, resolved_font_path, font_size)
    else:
        base_font = load_base_font(resolved_font_path, font_size)
        segments = [(text, "other", base_font)]
        target_h = 0

    # 2. 测量可视尺寸（用于参考）
    bw, top_min, bottom_max = measure_text_block(segments)
    if bw <= 0:
        raise ValueError(f"文字宽度为 0（text={text!r}），请检查文本内容/字体")

    # 3. 建立安全画布，避免因为原工具的 dy 垂直居中逻辑导致上下被切掉
    SAFE_PAD = 50
    canvas_w = bw + SAFE_PAD * 2
    canvas_h = (bottom_max - top_min) + SAFE_PAD * 2

    text_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_img)

    # 4. 反算起点
    first_seg_text = segments[0][0] if segments else ""
    first_b = segments[0][2].getbbox(first_seg_text, anchor="ls") if first_seg_text else (0, 0, 0, 0)
    
    start_x = SAFE_PAD - first_b[0]
    baseline_y = SAFE_PAD + abs(top_min) 

    render_text_on_canvas(
        text_img, draw,
        start_x, baseline_y,
        segments, text_color, target_h,
    )

    # 5. 自动裁掉四周多余的透明边缘，获取最精准的文字图片
    bbox = text_img.getbbox()
    if bbox:
        text_img = text_img.crop(bbox)
    else:
        raise ValueError(f"渲染后未获取到有效文字像素（text={text!r}）")
    
    real_w, real_h = text_img.size

    # 6. 保存
    text_image_path = os.path.join(work_dir, f"text_{index:03d}.png")
    text_img.save(text_image_path)

    meta = {
        "index": index,
        "text": text,
        "text_image": text_image_path,
        "width": real_w,
        "height": real_h,
        "font_path": font_path,
        "font_size": font_size,
        "text_color": text_color,
        "match_digit_height": match_digit_height,
        "blur_radius": cfg["blur_radius"],
        "offset_left": int(cfg["offset_left"]),
        "offset_bottom": int(cfg["offset_bottom"]),
    }
    print(f"[1/2] 文字图 #{index:03d} 已生成: {text_image_path}  ({real_w}x{real_h})  text={text!r}")
    return meta


def generate_text_images(image_path, common_config, text_items, work_dir):
    os.makedirs(work_dir, exist_ok=True)
    metas = []
    for i, item in enumerate(text_items):
        if not isinstance(item, dict):
            raise TypeError(f"text_items[{i}] 必须是 dict，实际为 {type(item)}")
        if "text" not in item:
            raise KeyError(f"text_items[{i}] 缺少 'text' 字段")

        # 【关键修改】解析文本时，把 image_path 传进去
        text = _resolve_text(item["text"], image_path)
        
        if not text.strip():
            print(f"[warn] text_items[{i}] 文本为空，跳过")
            continue

        cfg = _merge_config(common_config, item)
        meta = _render_one_text_image(text, cfg, work_dir, len(metas))
        metas.append(meta)

    if not metas:
        raise ValueError("没有任何有效文本项可渲染")

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
        print(f"[warn] 文字 #{meta['index']:03d} 可能超出画布: "
              f"pos=({block_x},{block_y}) size=({bw}x{bh}) canvas=({canvas_w}x{canvas_h})")

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


def compose_text_images(image_path, metas, config, output_dir=None):
    base = Image.open(image_path).convert("RGBA")
    result = base
    for meta in metas:
        result = _paste_one_text(result, meta)

    output_path = config.get("output_path", None) if config else None
    overwrite   = config.get("overwrite", True) if config else True

    if output_path is None:
        base_name, ext = os.path.splitext(os.path.basename(image_path))
        ext = ext or ".png"
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(image_path))
        os.makedirs(output_dir, exist_ok=True)
        joined = "_".join(safe_filename(m["text"])[:10] for m in metas)[:60]
        output_path = os.path.join(output_dir, f"{base_name}_{joined}{ext}")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if os.path.exists(output_path) and not overwrite:
            raise FileExistsError(f"输出文件已存在: {output_path}")

    save_ext = os.path.splitext(output_path)[1].lower()
    if save_ext in (".jpg", ".jpeg"):
        result.convert("RGB").save(output_path, quality=95)
    else:
        result.save(output_path)

    print(f"[2/2] 图片已生成: {output_path}")
    return output_path


# ============================================================
# 主流程
# ============================================================

def draw_texts_on_image(
    image_path,
    text_items,
    common_config=None,
    output_dir=None,
    work_root=None,
    keep_work_dir=True,
    output_config=None,
):
    if common_config is None:
        common_config = {}
    if output_config is None:
        output_config = {}

    if work_root is None:
        work_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watermarks")
    task_id  = uuid.uuid4().hex[:8]
    work_dir = os.path.join(work_root, task_id)

    try:
        print(f"[1/2] 生成文字图片 → {work_dir}")
        # 【关键修改】把 image_path 传给生成函数
        metas = generate_text_images(image_path, common_config, text_items, work_dir)

        print(f"[2/2] 合成到 {image_path}")
        output_path = compose_text_images(image_path, metas, output_config, output_dir=output_dir)

        return output_path

    finally:
        if not keep_work_dir:
            try:
                shutil.rmtree(work_dir)
            except Exception:
                pass
        else:
            print(f"[keep] 临时文件夹保留: {work_dir}")


def draw_text_on_image(image_path, text, output_dir=None, config=None, **kwargs):
    """单文本兼容包装"""
    config = config or {}
    common = {k: v for k, v in config.items() if k not in ("offset_left", "offset_bottom", "output_path", "overwrite")}
    item = {
        "text": text,
        "offset_left": config.get("offset_left", 0),
        "offset_bottom": config.get("offset_bottom", 0)
    }
    output_config = {"output_path": config.get("output_path"), "overwrite": config.get("overwrite", True)}
    return draw_texts_on_image(
        image_path=image_path,
        text_items=[item],
        common_config=common,
        output_dir=output_dir,
        output_config=output_config,
        **kwargs,
    )


# ============================================================
# 示例：演示如何从图片地址中提取文字
# ============================================================

if __name__ == "__main__":
    from plugins.get_font_path import get_font_path

    # 假设图片文件名是 "IMG_20260812_093000.jpg"
    # 我们写一个能接收 image_path 的函数，从中提取日期
    def extract_date_from_path(img_path):
        import os
        import re
        filename = os.path.basename(img_path)
        print(img_path)
        return "未知日期"

    image_path = "/Volumes/西数4T外置/百度网盘默认下载/test/IMG_20260812_093000.jpg"
    output_dir = "/Volumes/西数4T外置/百度网盘默认下载/test"

    common_config = {
        "font_path": get_font_path("苹方黑体-中粗-简.ttf"),
        "font_size": 36,
        "text_color": "#000000",
        "match_digit_height": True,
        "blur_radius": 0.0,
    }

    text_items = [
        {
            # 这里传入接收 image_path 的函数，内部动态获取文字
            "text": extract_date_from_path,
            "offset_left": 20,
            "offset_bottom": 20,
        },
        {
            # 兼容以前无参函数的写法
            "text": lambda: "© MyBrand",
            "offset_left": 600,
            "offset_bottom": 20,
            "font_size": 24,
            "text_color": "#FF0000",
        },
        {
            # 静态文本依然支持
            "text": "Sample",
            "offset_left": 20,
            "offset_bottom": 200,
            # "font_path": get_font_path("Arial.ttf"),
            "font_size": 48,
            "blur_radius": 1.5,
        },
    ]

    draw_texts_on_image(
        image_path=image_path,
        text_items=text_items,
        common_config=common_config,
        output_dir=output_dir,
        keep_work_dir=True,
    )