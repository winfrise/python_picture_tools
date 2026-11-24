import os
import re
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ============================================================
# 1. 基础工具函数
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
# 核心渲染逻辑：修复缺字检测机制
# ============================================================
def _is_char_supported(char, font):
    """✨ 精确检测字体是否支持某个字符"""
    if not char.strip(): return True
    try:
        # 获取未知字符的 advance 宽度（Pillow 对不支持的字符通常有一个固定的占位宽度）
        # \uffff 是一个绝对不存在的特殊字符，用它来测试兜底宽度
        notdef_width = font.getlength("\uffff")
        char_width = font.getlength(char)
        
        # 如果宽度一致，说明该字体不支持这个字，渲染出来可能是个方框
        if char_width == notdef_width:
            return False
        
        # 双重检测：尝试获取字体的 mask bbox，如果为空说明没画出任何东西
        mask = font.getmask(char)
        if not mask.getbbox():
            return False
            
        return True
    except Exception:
        return False

def _render_text(text, cfg):
    """渲染纯文字为透明PNG"""
    font_path = cfg.get("font_path")
    font_size = cfg.get("font_size", 40)
    text_color = cfg.get("text_color", "white")
    check_glyphs = cfg.get("check_glyphs", False)
    
    primary_font = _load_font(font_path, font_size)
    
    # --- 分支 A：常规渲染（默认） ---
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

    # --- 分支 B：开启字库检测，智能分字体渲染 ---
    else:
        # 兜底字体可以使用系统默认中文字体（这里用微软雅黑兜底，Mac 用户如果报错可以改成苹方）
        fallback_font = _load_font("msyh.ttc", font_size) 
        
        # 1. 拆分字符，不支持的直接换 fallback
        segments = []
        for char in text:
            if _is_char_supported(char, primary_font):
                segments.append((char, primary_font))
            else:
                segments.append((char, fallback_font))

        # 2. 合并相邻的相同字体字符
        merged_segments = []
        for char, f in segments:
            if merged_segments and merged_segments[-1][1] == f:
                merged_segments[-1] = (merged_segments[-1][0] + char, f)
            else:
                merged_segments.append((char, f))

        # 3. 计算尺寸 (绝对高度采用主字体或回退字体中最大的)
        total_w = 0
        top_min = 0
        bottom_max = 0
        for seg_text, f in merged_segments:
            if not seg_text: continue
            b = f.getbbox(seg_text, anchor="ls") 
            total_w += (b[2] - b[0])
            top_min = min(top_min, b[1])
            bottom_max = max(bottom_max, b[3])
            
        if total_w <= 0: return None

        pad = 100
        canvas_w = total_w + pad * 2
        canvas_h = (bottom_max - top_min) + pad * 2
        img = Image.new("RGBA", (canvas_w, canvas_h), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        start_x = pad
        baseline_y = pad + abs(top_min)

        # 4. 画阴影
        if cfg.get("shadow_color") and cfg["shadow_color"][3] > 0:
            s_layer = Image.new("RGBA", img.size, (0,0,0,0))
            s_draw = ImageDraw.Draw(s_layer)
            off = cfg.get("shadow_offset", (3,3))
            cur_x = start_x + off[0]
            cur_y = baseline_y + off[1]
            for seg_text, f in merged_segments:
                s_draw.text((cur_x, cur_y), seg_text, font=f, fill=cfg["shadow_color"], anchor="ls")
                cur_x += f.getlength(seg_text)
            if cfg.get("shadow_blur", 0) > 0:
                s_layer = s_layer.filter(ImageFilter.GaussianBlur(cfg["shadow_blur"]))
            img.alpha_composite(s_layer)

        # 5. 画文字主体
        cur_x = start_x
        for seg_text, f in merged_segments:
            draw.text((cur_x, baseline_y), seg_text, font=f, fill=text_color, anchor="ls")
            cur_x += f.getlength(seg_text)
        
        final_img = img

    # 蒙版与裁剪
    if cfg.get("texture_mask", False):
        mask = Image.new("L", final_img.size, 255)
        m_draw = ImageDraw.Draw(mask)
        tx1, ty1, tx2, ty2 = final_img.getbbox()
        if tx1 is not None:
            for _ in range(40):
                x0 = random.randint(tx1, tx2)
                y0 = random.randint(ty1, ty2)
                m_draw.rectangle([x0, y0, x0 + random.randint(20, 80), y0 + random.randint(20, 80)], fill=random.randint(80, 200))
            r,g,b,a = final_img.split()
            final_img = Image.merge("RGBA", (r,g,b, Image.composite(a, Image.new("L", a.size, 0), mask)))

    final_bbox = final_img.getbbox()
    return final_img.crop(final_bbox) if final_bbox else None

# ============================================================
# 2. 网格布局引擎 (无需修改，直接复制之前的)
# ============================================================
def render_rows(rows_config, texts_dict, global_cfg, image_path=None, total_width=None):
    # 略：与上一个版本完全一致
    rows_data = []
    for row in rows_config:
        row_align_y = row.get("align_y", "center")
        row_spacing = row.get("spacing", 15)
        row_cells = []
        for cell in row.get("cells", []):
            c_type = cell.get("type", "text")
            final_cfg = {**global_cfg, **cell}
            
            if c_type == "text":
                text_val = _resolve_text_value(cell.get("text_key", ""), texts_dict, image_path)
                img = _render_text(text_val, final_cfg) 
                row_cells.append({"img": img, "cfg": final_cfg})
            elif c_type == "group":
                img = render_rows(cell["rows"], texts_dict, global_cfg, image_path, total_width=cell.get("width", None))
                row_cells.append({"img": img, "cfg": final_cfg})
            else:
                row_cells.append({"img": None, "cfg": final_cfg})
        rows_data.append({"cells": row_cells, "align_y": row_align_y, "spacing": row_spacing})
        
    row_heights = [max([item["img"].height for item in r["cells"] if item["img"]] + [0]) for r in rows_data]
    for r_idx, r in enumerate(rows_data):
        for item in r["cells"]:
            if item["cfg"].get("type") == "divider":
                item["img"] = Image.new("RGBA", (item["cfg"].get("width", 6), row_heights[r_idx]), item["cfg"].get("color", (255, 165, 0, 255)))

    row_spacings = [r["spacing"] for r in rows_data]
    total_height = sum(row_heights) + sum(row_spacings[:-1]) if row_heights else 0
    if total_height <= 0: return None

    if total_width is None:
        max_row_w = 0
        for r in rows_data:
            row_w = sum(item["cfg"].get("width", item["img"].width if item["img"] else 0) for item in r["cells"])
            max_row_w = max(max_row_w, row_w)
        total_width = max_row_w

    canvas = Image.new("RGBA", (total_width, total_height), (0,0,0,0))
    current_y = 0
    for r_idx, r in enumerate(rows_data):
        row_h = row_heights[r_idx]
        row_align_y = r["align_y"]
        current_x = 0
        for item in r["cells"]:
            cfg = item["cfg"]
            img = item["img"]
            cell_w = cfg.get("width", img.width if img else 0)
            if img:
                align_x = cfg.get("align_x", "center")
                x_offset = 0 if align_x == "left" else (cell_w - img.width) if align_x == "right" else (cell_w - img.width) // 2
                y_offset = 0 if row_align_y == "top" else (row_h - img.height) if row_align_y == "bottom" else (row_h - img.height) // 2
                canvas.alpha_composite(img, (current_x + max(0, x_offset), current_y + max(0, y_offset)))
            current_x += cell_w
        current_y += row_h + (r["spacing"] if r_idx < len(row_spacings) else 0)

    return canvas

def render_component_to_image(background_path, output_path, layout_config, texts, common_config=None, pos_x=50, pos_y=50):
    # 略：与上一个版本完全一致
    if common_config is None: common_config = {}
    layer_img = render_rows(layout_config, texts, global_cfg=common_config, image_path=background_path)
    if not layer_img: return

    if background_path and os.path.exists(background_path):
        base_img = Image.open(background_path).convert("RGBA")
    else:
        base_img = Image.new("RGBA", (1920, 1080), (40, 40, 45, 255))

    bg_w, bg_h = base_img.size
    final_x = pos_x if pos_x >= 0 else bg_w - layer_img.width + pos_x
    final_y = pos_y if pos_y >= 0 else bg_h - layer_img.height + pos_y

    base_img.alpha_composite(layer_img, (final_x, final_y))
    
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"): base_img.convert("RGB").save(output_path, quality=95)
    else: base_img.save(output_path)