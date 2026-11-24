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
        try:
            return val(image_path) if image_path else val()
        except TypeError:
            return val()
    return val

def _resolve_text_value(text_key, texts_dict, image_path=None):
    if text_key not in texts_dict:
        return str(text_key)

    val = _eval_value(texts_dict[text_key], image_path)
    text = str(val) if val is not None else ""

    def _replace(match):
        k = match.group(1)
        if k in texts_dict:
            sub_val = _eval_value(texts_dict[k], image_path)
            return str(sub_val) if sub_val is not None else ""
        return match.group(0)
    
    text = re.sub(r'\{([a-zA-Z0-9_]+)\}', _replace, text)
    return text

def _render_text(text, cfg):
    font = _load_font(cfg.get("font_path"), cfg.get("font_size", 40))
    text_color = cfg.get("text_color", "white")
    
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = dummy.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    pad = 100
    img = Image.new("RGBA", (w + pad*2, h + pad*2), (0,0,0,0))
    draw_x, draw_y = pad - bbox[0], pad - bbox[1]
    
    if cfg.get("shadow_color") and cfg["shadow_color"][3] > 0:
        s_layer = Image.new("RGBA", img.size, (0,0,0,0))
        s_draw = ImageDraw.Draw(s_layer)
        off = cfg.get("shadow_offset", (3,3))
        s_draw.text((draw_x+off[0], draw_y+off[1]), text, font=font, fill=cfg["shadow_color"])
        if cfg.get("shadow_blur", 0) > 0:
            s_layer = s_layer.filter(ImageFilter.GaussianBlur(cfg["shadow_blur"]))
        img.alpha_composite(s_layer)

    ImageDraw.Draw(img).text((draw_x, draw_y), text, font=font, fill=text_color)
    
    if cfg.get("texture_mask", False):
        mask = Image.new("L", img.size, 255)
        m_draw = ImageDraw.Draw(mask)
        tx1, ty1, tx2, ty2 = img.getbbox()
        if tx1 is not None:
            for _ in range(40):
                x0 = random.randint(tx1, tx2)
                y0 = random.randint(ty1, ty2)
                m_draw.rectangle([x0, y0, x0 + random.randint(20, 80), y0 + random.randint(20, 80)], fill=random.randint(80, 200))
            r,g,b,a = img.split()
            img = Image.merge("RGBA", (r,g,b, Image.composite(a, Image.new("L", a.size, 0), mask)))

    final_bbox = img.getbbox()
    return img.crop(final_bbox) if final_bbox else None

def _create_divider(height, width=8, color=(255, 165, 0, 255)):
    return Image.new("RGBA", (width, height), color)

# ============================================================
# 2. 网格布局引擎
# ============================================================
def render_rows(rows_config, texts_dict, image_path=None, total_width=None):
    rows_data = []
    for row in rows_config:
        row_cells = []
        # 增加判断：确保 row 是个字典
        if not isinstance(row, dict):
            raise TypeError(f"Layout config 格式错误：row 应该是一个字典，但你传入的是 {type(row)} -> {row}")
            
        for cell in row.get("cells", []):
            c_type = cell.get("type", "text")
            
            if c_type == "text":
                text_val = _resolve_text_value(cell.get("text_key", ""), texts_dict, image_path)
                img = _render_text(text_val, cell)
            elif c_type == "group":
                group_w = cell.get("width", None)
                img = render_rows(cell["rows"], texts_dict, image_path, total_width=group_w)
            elif c_type == "divider":
                img = None 
            else:
                img = None
            
            row_cells.append({"img": img, "cfg": cell})
        rows_data.append(row_cells)
        
    row_heights = [max([item["img"].height for item in rc if item["img"]] + [0]) for rc in rows_data]
        
    for r_idx, row_cells in enumerate(rows_data):
        for item in row_cells:
            if item["cfg"].get("type") == "divider":
                item["img"] = _create_divider(
                    height=row_heights[r_idx], 
                    width=item["cfg"].get("width", 6),
                    color=item["cfg"].get("color", (255, 165, 0, 255))
                )

    row_spacings = [row.get("spacing", 15) for row in rows_config]
    total_height = sum(row_heights) + sum(row_spacings[:-1]) if row_heights else 0
    if total_height <= 0: return None

    if total_width is None:
        max_row_w = 0
        for row_cells in rows_data:
            row_w = sum(item["cfg"].get("width", item["img"].width if item["img"] else 0) for item in row_cells)
            max_row_w = max(max_row_w, row_w)
        total_width = max_row_w

    canvas = Image.new("RGBA", (total_width, total_height), (0,0,0,0))
    
    current_y = 0
    for r_idx, row_cells in enumerate(rows_data):
        row_h = row_heights[r_idx]
        row_align_y = rows_config[r_idx].get("align_y", "center")
        
        current_x = 0
        for item in row_cells:
            cfg = item["cfg"]
            img = item["img"]
            cell_w = cfg.get("width", img.width if img else 0)
            
            if img:
                align_x = cfg.get("align_x", "left")
                x_offset = 0 if align_x == "left" else (cell_w - img.width) if align_x == "right" else (cell_w - img.width) // 2
                y_offset = 0 if row_align_y == "top" else (row_h - img.height) if row_align_y == "bottom" else (row_h - img.height) // 2
                canvas.alpha_composite(img, (current_x + max(0, x_offset), current_y + max(0, y_offset)))
                
            current_x += cell_w
            
        current_y += row_h + (row_spacings[r_idx] if r_idx < len(row_spacings) else 0)

    return canvas

# ============================================================
# 3. 对外暴露的 API
# ============================================================
def render_component_to_image(background_path, output_path, layout_config, texts, pos_x=50, pos_y=50):
    print(f"▶ 正在渲染布局组件...")
    
    # 增加一个格式检查
    if not isinstance(layout_config, list):
         raise TypeError(f"layout_config 必须是一个列表(list)，你传入的是 {type(layout_config)}")

    layer_img = render_rows(layout_config, texts, image_path=background_path)
    
    if not layer_img:
        print("❌ 渲染失败，未生成任何有效图像。")
        return

    if background_path and os.path.exists(background_path):
        base_img = Image.open(background_path).convert("RGBA")
    else:
        base_img = Image.new("RGBA", (1920, 1080), (40, 40, 45, 255))

    bg_w, bg_h = base_img.size
    final_x = pos_x if pos_x >= 0 else bg_w - layer_img.width + pos_x
    final_y = pos_y if pos_y >= 0 else bg_h - layer_img.height + pos_y

    base_img.alpha_composite(layer_img, (final_x, final_y))
    
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        base_img.convert("RGB").save(output_path, quality=95)
    else:
        base_img.save(output_path)
    print(f"✅ 渲染成功: {output_path}")
