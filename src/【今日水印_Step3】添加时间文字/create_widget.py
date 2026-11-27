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
    # ---- ✨ 图片替换文字（精准避开阴影，只贴文字本体）----
    mask_cfg = cfg.get("image_mask")
    if isinstance(mask_cfg, dict):
        mask_path = mask_cfg.get("path")
        if mask_path and os.path.exists(mask_path):
            
            # 1. 重新生成一个【纯文字（无阴影）】的透明图层
            # 这是为了排除阴影的干扰，确保波浪图只贴在文字本身上
            text_only_img = Image.new("RGBA", final_img.size, (0,0,0,0))
            draw_text = ImageDraw.Draw(text_only_img)
            
            # 因为前面生成文字时有 pad=100 和坐标计算，我们直接从当前配置里取回坐标
            # 重新画一遍纯文字
            if not check_glyphs:
                draw_text.text((draw_x, draw_y), text, font=primary_font, fill=text_color)
            else:
                cur_x = start_x
                for seg_text, f in merged_segments:
                    draw_text.text((cur_x, baseline_y), seg_text, font=f, fill=text_color, anchor="ls")
                    cur_x += f.getlength(seg_text)
            
            # 提取纯文字的 Alpha 轮廓
            text_alpha = text_only_img.split()[3]
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

            # 3. 创建画布并贴合波浪图
            target_w, target_h = final_img.size
            wave_img = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            pos_x, pos_y = mask_cfg.get("pos", (0, 0))
            wave_img.alpha_composite(mask_img, (pos_x, pos_y))

            # 4. ✨ 核心：让纯文字蒙版向内收缩像素
            shrink_px = mask_cfg.get("shrink", 2)
            if shrink_px > 0:
                filter_size = shrink_px * 2 + 1
                text_alpha = text_alpha.filter(ImageFilter.MinFilter(filter_size))

            # 5. 将收缩后的纯文字轮廓，套用到波浪图上
            wave_img.putalpha(ImageChops.multiply(wave_img.split()[3], text_alpha))

            # 6. 叠加原图（带阴影的文字）和波浪图
            result_img = Image.alpha_composite(final_img, wave_img)

            # 7. 裁剪返回
            final_bbox = result_img.getbbox()
            return result_img.crop(final_bbox) if final_bbox else None
        
    # 如果没有配置 image_mask，正常返回原本的文字
    final_bbox = final_img.getbbox()
    return final_img.crop(final_bbox) if final_bbox else None

def _render_multiline_text(text, cfg):
    # 1. 基础配置
    font_path = cfg.get("font_path")
    font_size = cfg.get("font_size", 40)
    primary_font = _load_font(font_path, font_size)
    wrap_width = cfg.get("wrap_width")
    
    def _measure(s, f):
        try: return f.getlength(s)
        except: 
            bbox = f.getbbox(s)
            return bbox[2] - bbox[0] if bbox else 0

    # 2. 自动换行 + 清理每行首尾多余空格
    raw_lines = text.split("\n")
    lines = []
    for raw in raw_lines:
        if wrap_width is None or _measure(raw, primary_font) <= wrap_width:
            lines.append(raw.strip())  # 去掉首尾空格
            continue
        
        cur = ""
        for ch in raw:
            if _measure(cur + ch, primary_font) <= wrap_width or not cur:
                cur += ch
            else:
                lines.append(cur.strip())
                cur = ch
        if cur:
            lines.append(cur.strip())

    if not lines:
        lines = [""]

    # 3. 逐行渲染并裁切
    line_imgs = []
    for line in lines:
        if line:
            img = _render_text(line, cfg)
            if img:
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                line_imgs.append(img)
            else:
                line_imgs.append(None)
        else:
            line_imgs.append(None)

    # 4. 计算统一的行高
    line_height_ratio = cfg.get("line_height", 1.2)
    ref_img = next((im for im in line_imgs if im), None)
    base_line_h = int(ref_img.height * line_height_ratio) if ref_img else int(font_size * line_height_ratio)
    
    line_step = base_line_h + cfg.get("default_line_spacing", 0)

    # 5. ✨ 核心修复：按【行】真实文字宽度计算画布总宽，而不是用图片宽度
    # 这样即便因为阴影或标点导致图片有透明边距，也不影响整体对齐
    valid_widths = [_measure(l, primary_font) for l in lines if l]
    total_w = max(valid_widths) if valid_widths else 1

    # 为了防止阴影或波浪图超出了测量宽度，留一点点安全边距
    total_w = int(total_w + cfg.get("font_size", 40) * 0.5) 

    total_h = line_step * (len(line_imgs) - 1) + base_line_h
    canvas = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    
    align = cfg.get("align", "left")
    
    # 6. 绘制到画布
    for i, im in enumerate(line_imgs):
        if not im:
            continue
        
        # 因为 im 已经去除了透明边距，直接用图片宽度计算坐标即可
        if align == "center":
            x = (total_w - im.width) // 2
        elif align == "right":
            x = total_w - im.width
        else:
            x = 0
            
        y = i * line_step + (base_line_h - im.height) // 2
        canvas.alpha_composite(im, (int(x), int(y)))

    # 7. 最终裁切返回
    final_bbox = canvas.getbbox()
    return canvas.crop(final_bbox) if final_bbox else None

# ============================================================
# 2. 网格布局引擎 (保持不变)
# ============================================================
def render_rows(rows_config, texts_dict, global_cfg, image_path=None, total_width=None):
    rows_data = []
    
    # 1. 解析所有单元格
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
                        
            elif c_type == "image":
                img_path = _resolve_text_value(cell.get("text_key", ""), texts_dict, image_path)
                if img_path and os.path.exists(img_path):
                    img = Image.open(img_path).convert("RGBA")
                    
                    target_w = cell.get("width")
                    target_h = cell.get("height")
                    
                    if target_w is not None and target_h is not None:
                        img = img.resize((int(target_w), int(target_h)), Image.LANCZOS)
                    elif target_w is not None:
                        ratio = target_w / img.width
                        new_h = max(1, int(round(img.height * ratio)))
                        img = img.resize((int(target_w), new_h), Image.LANCZOS)
                    elif target_h is not None:
                        ratio = target_h / img.height
                        new_w = max(1, int(round(img.width * ratio)))
                        img = img.resize((new_w, int(target_h)), Image.LANCZOS)

            elif c_type == "multiline_text":
                text_val = _resolve_text_value(cell.get("text_key", ""), texts_dict, image_path)
                img = _render_multiline_text(text_val, final_cfg)
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
            
        rows_data.append({
            "cells": row_cells, 
            "spacing": row.get("spacing", 0),
            "align_x": row.get("align_x", "left") 
        })
        
    # 2. 计算每行的实际高度和实际总宽度
    row_heights = []
    row_widths = []
    for r in rows_data:
        max_h = 0
        row_w = 0
        for item in r["cells"]:
            max_h = max(max_h, item["cell_h"])
            row_w += item["cell_w"]
        row_heights.append(max_h)
        row_widths.append(row_w)

    # 3. 渲染分割线
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

    # 4. 计算画布整体尺寸
    row_spacings = [r["spacing"] for r in rows_data]
    # ✨ 修正 1：计算总高度时，忽略最后一行的 spacing
    total_height = sum(row_heights) + sum(row_spacings[:-1]) if row_heights else 0
    if total_height <= 0: return None

    if total_width is None:
        total_width = max(row_widths) if row_widths else 0

    # 补偿逻辑 (处理负数偏移)
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

    # 5. 绘制到画布
    current_y = shift_y
    for r_idx, r in enumerate(rows_data):
        row_h = row_heights[r_idx]
        actual_row_w = row_widths[r_idx]
        
        # ✨ 核心：根据 align_x 计算当前行的起始 X 坐标
        align_x = r["align_x"]
        if align_x == "right":
            start_x = shift_x + (total_width - actual_row_w)
        elif align_x == "center":
            start_x = shift_x + (total_width - actual_row_w) // 2
        else: # 默认 left
            start_x = shift_x
            
        current_x = start_x
        
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
            
        # ✨ 修正 2：只有当不是最后一行时，才追加 spacing
        if r_idx < len(rows_data) - 1:
            current_y += row_h + r["spacing"]
        else:
            current_y += row_h

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
        temp_work_dir=None
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
    for idx, block in enumerate(layout_data):
        if not isinstance(block, dict):
            continue

        pos_x = block.get("pos_x", 0)
        pos_y = block.get("pos_y", 0)


        user_scale = block.get("scale") 
        standard_width = block.get('standard_width')

        # 2. 逻辑判断
        if user_scale:
            # 用户明确指定了缩放
            scale = user_scale
        elif standard_width and standard_width > 0:
            # 用户没指定，但有基准宽度 -> 自动计算填满背景
            scale = bg_w / standard_width
        else:
            # 既没指定缩放，也没基准宽度 -> 兜底默认 1.0
            scale = 1.0

        layout_config = block.get("layout_config", [])

        # 1. 针对当前的块，生成其相对排版图层
        layer_img = render_rows(
            rows_config=layout_config,
            texts_dict=texts, 
            global_cfg=common_config, 
            image_path=background_path
        )
        
        if not layer_img: 
            continue

        # ✨ 保存 layer_img 到临时目录（利用 output_path 保持目录结构）
        if temp_work_dir:
            os.makedirs(temp_work_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            save_path = os.path.join(temp_work_dir, f"{base_name}_layer_{idx}.png")
            print(save_path)
            layer_img.save(save_path)

        # 2. ✨ 如果配置了 scale，对排版图层进行整体缩放
        if scale != 1.0:
            new_w = max(1, int(layer_img.width * scale))
            new_h = max(1, int(layer_img.height * scale))
            # 使用 LANCZOS 保证缩放质量
            layer_img = layer_img.resize((new_w, new_h), Image.LANCZOS)

        # 3. 计算绝对坐标（支持负数从右/下对齐，且基于缩放后的 layer_img.width 计算）
        final_layer_x = pos_x if pos_x >= 0 else bg_w - layer_img.width + pos_x
        final_layer_y = pos_y if pos_y >= 0 else bg_h - layer_img.height + pos_y

        # 4. 将缩放后的当前块合成到背景上
        base_img.alpha_composite(layer_img, (int(final_layer_x), int(final_layer_y)))
    
    # 统一保存
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"): 
        base_img.convert("RGB").save(output_path, quality=95)
    else: 
        base_img.save(output_path)


# ============================================================
# 4. 批量处理文件夹 (新增)
# ============================================================
def batch_process_folder(
        input_dir, 
        output_dir, 
        layout_data, 
        texts, 
        common_config=None,
        temp_work_dir=None
    ):
    """
    遍历 input_dir 下的所有图片，应用水印，并按相同的目录结构输出到 output_dir。
    """
    if common_config is None: common_config = {}
    
    # 支持的图片后缀
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    
    count = 0
    for root, dirs, files in os.walk(input_dir):
        # 跳过以 . 开头的隐藏文件夹（如 .git, .DS_Store 所在文件夹等）
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            # 跳过隐藏文件
            if file.startswith('.'):
                continue
                
            ext = os.path.splitext(file)[1].lower()
            if ext not in valid_exts:
                continue
                
            input_path = os.path.join(root, file)
            
            # 计算相对路径，维持原目录结构
            rel_path = os.path.relpath(root, input_dir)
            # 如果有子文件夹，在输出目录中创建对应结构
            target_dir = os.path.join(output_dir, rel_path) if rel_path != "." else output_dir
            os.makedirs(target_dir, exist_ok=True)
            output_path = os.path.join(target_dir, file)
            print(f"[{count+1}] 处理中: {input_path} -> {output_path}")

            curr_temp_work_dir = os.path.join(temp_work_dir, rel_path) if rel_path != "." else temp_work_dir
            
            try:
                # 如果 layout_data 是函数，则可以根据不同的背景图动态生成排版（可选高级功能）
                current_layout = layout_data(input_path) if callable(layout_data) else layout_data
                current_texts = texts(input_path) if callable(texts) else texts

                render_component_to_image(
                    background_path=input_path,
                    output_path=output_path,
                    layout_data=current_layout,
                    texts=current_texts,
                    common_config=common_config,
                    temp_work_dir=curr_temp_work_dir
                )
                count += 1
            except Exception as e:
                print(f"❌ 处理失败: {input_path}, 错误信息: {e}")

    print(f"\n🎉 批量处理完成！共处理 {count} 张图片。输出目录: {output_dir}")