import os
import re
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

# ============================================================
# 1. 基础工具函数 (保持不变)
# ============================================================
def _load_font(font_path, size):
    if font_path and os.path.exists(font_path):
        try: return ImageFont.truetype(font_path, size)
        except: pass
    for f in ["msyh.ttc", "simhei.ttf", "/System/Library/Fonts/PingFang.ttc"]:
        if os.path.exists(f):
            try: return ImageFont.truetype(f, size)
            except: pass
    return ImageFont.load_default()

def _eval_value(val, image_path=None):
    if callable(val):
        try: return val(image_path) if image_path else val()
        except TypeError: return val()
    return val

def _resolve_text_value(text_key, texts_dict, image_path=None):
    if text_key not in texts_dict: return str(text_key)
    val = _eval_value(texts_dict[text_key], image_path)
    text = str(val) if val is not None else ""
    def _replace(match):
        k = match.group(1)
        if k in texts_dict:
            sub_val = _eval_value(texts_dict[k], image_path)
            return str(sub_val) if sub_val is not None else ""
        return match.group(0)
    return re.sub(r'\{([a-zA-Z0-9_]+)\}', _replace, text)

# ============================================================
# 核心渲染逻辑 (支持图片直接替换文字)
# ============================================================
def _is_char_supported(char, font):
    if not char.strip(): return True
    try:
        notdef_width = font.getlength("\uffff")
        char_width = font.getlength(char)
        if char_width == notdef_width: return False
        mask = font.getmask(char)
        if not mask.getbbox(): return False
        return True
    except Exception:
        return False

def _render_text(text, cfg):
    font_path = cfg.get("font_path")
    font_size = cfg.get("font_size", 40)
    text_color = cfg.get("text_color", "white")
    check_glyphs = cfg.get("check_glyphs", False)
    primary_font = _load_font(font_path, font_size)
    
    if not check_glyphs:
        dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bbox = dummy.textbbox((0, 0), text, font=primary_font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad = 100
        img = Image.new("RGBA", (w + pad*2, h + pad*2), (0,0,0,0))
        draw_x, draw_y = pad - bbox[0], pad - bbox[1]
        if cfg.get("shadow_color") and cfg["shadow_color"][3] > 0:
            s_layer = Image.new("RGBA", img.size, (0,0,0,0))
            s_draw = ImageDraw.Draw(s_layer)
            off = cfg.get("shadow_offset", (3,3))
            s_draw.text((draw_x+off[0], draw_y+off[1]), text, font=primary_font, fill=cfg["shadow_color"])
            if cfg.get("shadow_blur", 0) > 0:
                s_layer = s_layer.filter(ImageFilter.GaussianBlur(cfg["shadow_blur"]))
            img.alpha_composite(s_layer)
        ImageDraw.Draw(img).text((draw_x, draw_y), text, font=primary_font, fill=text_color)
        final_img = img
    else:
        fallback_font = _load_font(cfg.get("fallback_font") or "msyh.ttc", font_size)
        segments = []
        for char in text:
            if _is_char_supported(char, primary_font): segments.append((char, primary_font))
            else: segments.append((char, fallback_font))
        merged_segments = []
        for char, f in segments:
            if merged_segments and merged_segments[-1][1] == f: merged_segments[-1] = (merged_segments[-1][0] + char, f)
            else: merged_segments.append((char, f))
        
        total_w = 0; top_min = 0; bottom_max = 0
        for seg_text, f in merged_segments:
            if not seg_text: continue
            b = f.getbbox(seg_text, anchor="ls") 
            total_w += (b[2] - b[0]); top_min = min(top_min, b[1]); bottom_max = max(bottom_max, b[3])
        if total_w <= 0: return None
        pad = 100
        img = Image.new("RGBA", (total_w + pad*2, (bottom_max - top_min) + pad*2), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        start_x = pad; baseline_y = pad + abs(top_min)
        
        if cfg.get("shadow_color") and cfg["shadow_color"][3] > 0:
            s_layer = Image.new("RGBA", img.size, (0,0,0,0))
            s_draw = ImageDraw.Draw(s_layer)
            off = cfg.get("shadow_offset", (3,3))
            cur_x = start_x + off[0]; cur_y = baseline_y + off[1]
            for seg_text, f in merged_segments:
                s_draw.text((cur_x, cur_y), seg_text, font=f, fill=cfg["shadow_color"], anchor="ls")
                cur_x += f.getlength(seg_text)
            if cfg.get("shadow_blur", 0) > 0: s_layer = s_layer.filter(ImageFilter.GaussianBlur(cfg["shadow_blur"]))
            img.alpha_composite(s_layer)
        
        cur_x = start_x
        for seg_text, f in merged_segments:
            draw.text((cur_x, baseline_y), seg_text, font=f, fill=text_color, anchor="ls")
            cur_x += f.getlength(seg_text)
        final_img = img

    # ---- ✨ 图片直接替换文字轮廓（局部生效，完美消除黑边）----
    # ---- ✨ 图片直接替换文字轮廓（保留文字底色，只替换波浪线区域）----
    mask_cfg = cfg.get("image_mask")
    if isinstance(mask_cfg, dict):
        mask_path = mask_cfg.get("path")
        if mask_path and os.path.exists(mask_path):
            # 1. 提取文字轮廓
            text_alpha = final_img.split()[3]
            bbox = text_alpha.getbbox()
            if not bbox:
                return None

            # 2. 加载波浪图
            mask_img = Image.open(mask_path).convert("RGBA")
            sw = mask_cfg.get("scale_width", 1.0)
            sh = mask_cfg.get("scale_height", 1.0)
            new_w = max(1, int(round(mask_img.width * sw)))
            new_h = max(1, int(round(mask_img.height * sh)))
            if (new_w, new_h) != mask_img.size:
                mask_img = mask_img.resize((new_w, new_h), Image.LANCZOS)

            # 3. 创建与文字一样大的透明画布，把波浪图贴上去
            target_w, target_h = final_img.size
            wave_img = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            pos_x, pos_y = mask_cfg.get("pos", (0, 0))
            wave_img.alpha_composite(mask_img, (pos_x, pos_y))

            # 4. 将波浪图的轮廓套用上文字的形状（此时的 wave_img 只在文字笔画处有图案）
            wave_img.putalpha(ImageChops.multiply(wave_img.split()[3], text_alpha))

            # 5. 【核心】将原文字和波浪图叠加。
            # 这样文字作为底色（不会有透明缝隙），波浪图作为高亮覆盖在上面
            result_img = Image.alpha_composite(final_img, wave_img)

            # 6. 裁剪返回
            final_bbox = result_img.getbbox()
            return result_img.crop(final_bbox) if final_bbox else None
    # 如果没有配置 image_mask，正常返回原本的文字
    final_bbox = final_img.getbbox()
    return final_img.crop(final_bbox) if final_bbox else None
# ============================================================
# 2. 网格布局引擎 (保持不变)
# ============================================================
def render_rows(rows_config, texts_dict, global_cfg, image_path=None, total_width=None):
    rows_data = []
    
    for row in rows_config:
        row_cells = []
        for cell in row.get("cells", []):
            c_type = cell.get("type", "text")
            final_cfg = {**global_cfg, **cell}
            
            s_left = final_cfg.get("space_left", 0)
            s_right = final_cfg.get("space_right", 0)
            s_top = final_cfg.get("space_top", 0)
            s_bottom = final_cfg.get("space_bottom", 0)
            
            img = None
            if c_type == "text":
                text_val = _resolve_text_value(cell.get("text_key", ""), texts_dict, image_path)
                img = _render_text(text_val, final_cfg)
                if img:
                    wr = final_cfg.get("width_ratio", 1.0)
                    hr = final_cfg.get("height_ratio", 1.0)
                    if wr != 1.0 or hr != 1.0:
                        new_w = max(1, int(round(img.width * wr)))
                        new_h = max(1, int(round(img.height * hr)))
                        img = img.resize((new_w, new_h), Image.LANCZOS)

            elif c_type == "group":
                img = render_rows(cell["rows"], texts_dict, global_cfg, image_path, total_width=cell.get("width", None))
                
            if img:
                cell_w = img.width + s_left + s_right
                cell_h = img.height + s_top + s_bottom
            elif c_type == "divider":
                cell_w = final_cfg.get("width", 6) + s_left + s_right
                custom_h = final_cfg.get("height", None)
                cell_h = (custom_h + s_top + s_bottom) if custom_h is not None else 0
            else:
                cell_w = final_cfg.get("width", 0) + s_left + s_right
                cell_h = 0
                
            row_cells.append({
                "img": img, 
                "cfg": final_cfg,
                "cell_w": cell_w,
                "cell_h": cell_h
            })
        rows_data.append({"cells": row_cells, "spacing": row.get("spacing", 15)})
        
    row_heights = []
    for r in rows_data:
        max_h = 0
        for item in r["cells"]:
            max_h = max(max_h, item["cell_h"])
        row_heights.append(max_h)

    for r_idx, r in enumerate(rows_data):
        for item in r["cells"]:
            if item["cfg"].get("type") == "divider":
                line_w = item["cfg"].get("width", 6)
                custom_h = item["cfg"].get("height", None)
                line_h = custom_h if custom_h is not None else row_heights[r_idx]
                item["img"] = Image.new(
                    "RGBA",
                    (line_w, line_h),
                    item["cfg"].get("color", (255, 165, 0, 255))
                )

    row_spacings = [r["spacing"] for r in rows_data]
    total_height = sum(row_heights) + sum(row_spacings[:-1]) if row_heights else 0
    if total_height <= 0: return None

    if total_width is None:
        max_row_w = 0
        for r in rows_data:
            row_w = sum(item["cell_w"] for item in r["cells"])
            max_row_w = max(max_row_w, row_w)
        total_width = max_row_w

    min_x, min_y = 0, 0
    for r_idx, r in enumerate(rows_data):
        for item in r["cells"]:
            if item["img"]:
                ox = item["cfg"].get("offset_x", 0)
                oy = item["cfg"].get("offset_y", 0)
                min_x = min(min_x, ox)
                min_y = min(min_y, oy)
    
    shift_x = abs(min_x) if min_x < 0 else 0
    shift_y = abs(min_y) if min_y < 0 else 0

    canvas_w = total_width + shift_x
    canvas_h = total_height + shift_y
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0,0,0,0))

    current_y = shift_y
    for r_idx, r in enumerate(rows_data):
        row_h = row_heights[r_idx]
        current_x = shift_x
        
        for item in r["cells"]:
            cfg = item["cfg"]
            img = item["img"]
            
            off_x = cfg.get("offset_x", 0)
            off_y = cfg.get("offset_y", 0)
            
            if img:
                draw_x = current_x + cfg.get("space_left", 0) + off_x
                draw_y = current_y + cfg.get("space_top", 0) + off_y
                canvas.alpha_composite(img, (draw_x, draw_y))
                
            current_x += item["cell_w"]
            
        current_y += row_h + (r["spacing"] if r_idx < len(row_spacings) else 0)

    return canvas


# ============================================================
# 3. 对外暴露的 API (支持数组，绘制多个独立的块)
# ============================================================
def render_component_to_image(
        background_path, 
        output_path, 
        layout_data,  # 必须是 List[Dict]，每个 Dict 包含 pos_x, pos_y, layout_config
        texts, 
        common_config=None, 
    ):
    if common_config is None: common_config = {}

    # ✨ 严格校验：必须传入数组
    if not isinstance(layout_data, list):
        raise TypeError("layout_data 必须是一个列表（Array），即使只有一个块也要包在 [] 里！")

    # 加载背景
    if background_path and os.path.exists(background_path):
        base_img = Image.open(background_path).convert("RGBA")
    else:
        base_img = Image.new("RGBA", (1920, 1080), (40, 40, 45, 255))

    bg_w, bg_h = base_img.size

    # ✨ 遍历数组，依次绘制每一个独立的块
    for block in layout_data:
        if not isinstance(block, dict):
            continue

        pos_x = block.get("pos_x", 0)
        pos_y = block.get("pos_y", 0)
        layout_config = block.get("layout_config", [])

        # 针对当前的块，生成其相对排版图层
        layer_img = render_rows(
            rows_config=layout_config,
            texts_dict=texts, 
            global_cfg=common_config, 
            image_path=background_path
        )
        
        if not layer_img: 
            continue

        # 计算绝对坐标（支持负数从右/下对齐）
        final_layer_x = pos_x if pos_x >= 0 else bg_w - layer_img.width + pos_x
        final_layer_y = pos_y if pos_y >= 0 else bg_h - layer_img.height + pos_y

        # 将当前块合成到背景上
        base_img.alpha_composite(layer_img, (final_layer_x, final_layer_y))
    
    # 统一保存
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"): 
        base_img.convert("RGB").save(output_path, quality=95)
    else: 
        base_img.save(output_path)