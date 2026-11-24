from create_widget import render_component_to_image
from datetime import datetime
import os

# ================= 使用示例 =================
if __name__ == "__main__":
    
    # --- 1. 准备数据字典 ---
    date_val = "2026-11-03"
    def get_week(d):
        try: return ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][datetime.strptime(d, "%Y-%m-%d").weekday()]
        except: return "未知"
        
    my_texts = {
        "time": "12:47",
        "date": date_val,
        "weather": "阴",
        "temp": "15℃",
        "week": lambda: get_week(date_val),
        "weather_line": "{week} {weather} {temp}",
        "location": "漳州市龙海区·福建华夏高级技工学校(龙江校区)"
    }

    # --- 2. 准备布局 (请确保完全复制这部分，不要把 [ ] 和 { } 漏掉) ---
    my_layout = [
        {
            "align_y": "center",
            "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/苹方黑体-中黑-简.ttf",
            "font_size": 47,
            "text_color": (255,255,255,255),
            "shadow_offset": (4,4), 
            "shadow_blur": 3, 
            "align_x": "left", 
            "cells": [
                { # 时间
                    "type": "text", 
                    "text_key": "time", 
                    "width": 320,
                    "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/jinrishuiyin.ttf",
                    "font_size": 148, 
                    "texture_mask": False
                },
                {
                    "type": "divider", 
                    "width": 8, 
                    "color": (255, 165, 0, 255)
                },
                {
                    "type": "group", 
                    "width": 450, 
                    "align_x": "left",
                    "rows": [
                        {
                            "align_y": "bottom", 
                            "spacing": 0,
                            "cells": [
                                {
                                    "type": "text", 
                                    "text_key": "date", 
                                    "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/jinrishuiyin.ttf",
                                    "font_size": 56,
                                }
                            ]
                        },
                        {
                            "align_y": "top", 
                            "spacing": 0,
                            "cells": [
                                {
                                    "type": "text", 
                                    "text_key": "weather_line", 
                                    "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/苹方黑体-中黑-简.ttf",
                                    "width": 450,
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "align_y": "center",
            "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/苹方黑体-中粗-简.ttf",
            "font_size": 47,
            "text_color": (255,255,255,255),
            "shadow_offset": (4,4), 
            "shadow_blur": 3, 
            "align_x": "left", 
            "cells": [
                { # 时间
                    "type": "text", 
                    "text_key": "location", 
                }
            ]
        }
    ]

    background_path = "/Users/teacher/Desktop/5张/01.png"
    base_name, ext = os.path.splitext(background_path)
    output_path = f"{base_name}_加水印{ext}"
    # --- 3. 开始渲染 ---
    render_component_to_image(
        background_path=background_path, # 这里可以替换成实际的背景图片路径
        output_path=output_path,
        layout_config=my_layout,
        texts=my_texts,
        pos_x=44,
        pos_y=-44
    )