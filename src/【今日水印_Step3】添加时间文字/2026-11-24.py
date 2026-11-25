from create_widget import render_component_to_image
from datetime import datetime
import os

if __name__ == "__main__":
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
        "location": "漳州市龙海区·福建华夏高级技工学校(龙江校区)",
        "logo": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/【今日水印_Step3】添加时间文字/assets/jinrishuiyin.png",
        "sn_code": "KTHAN1E3Y3X3BP"
    }

    # ✨ 公共配置（相当于 CSS 的 body 选择器）
    my_common_config = {
        "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/苹方黑体-中粗-简.ttf",
        "font_size": 47,
        "text_color": (255, 255, 255, 255),
        "shadow_color": (0, 0, 0, 100),
        "shadow_offset": (2, 2), 
        "shadow_blur": 3, 
        "align_x": "left",
        "spacing": 0
    }

    layout_data = [
        {
            "pos_x":44,
            "pos_y": -544,
            "layout_config":[
                {
                    "align_y": "center",
                    "cells": [
                        { 
                            "type": "text", 
                            "text_key": "time", 
                            # 时间和公共配置不同，单独指定
                            "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/jinrishuiyin.ttf",
                            "font_size": 148,
                            "image_mask": {
                                "path": "/Users/teacher/Desktop/111.png", 
                                # "path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/【今日水印_Step3】添加时间文字/assets/time_mask.png",
                                "pos": (0, 0),                # 蒙版相对文字左上角的偏移，默认 (0, 0)
                                "scale_width": 0.5,           # 宽度缩放比例，默认 1.0
                                "scale_height": 0.5,          # 高度缩放比例，默认 1.0
                            },
                        },
                        {
                            "type": "divider", 
                            "width": 8, 
                            # "height": 20,
                            "color": (253, 205, 67, 255),
                            "space_left": 40,
                            "space_right": 40,
                        },
                        {
                            "type": "group", 
                            "width": 450, 
                            "rows": [
                                {
                                    "cells": [
                                        {
                                            "type": "text", 
                                            "text_key": "date", 
                                            "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/jinrishuiyin.ttf",
                                            "font_size": 56,
                                            "check_glyphs": True,
                                            "fallback_font": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/苹方黑体-中黑-简.ttf" 
                                        }
                                    ]
                                },
                                {
                                    "cells": [
                                        {
                                            "type": "text", 
                                            "text_key": "weather_line", 
                                            "space_top": 0,
                                            "width_ratio": 0.9
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "align_y": "center",
                    "cells": [
                        { 
                            "type": "text", 
                            "text_key": "location",
                            "space_top": 40
                        }
                    ]
                }
            ]
        },
        {
            "pos_x": -44,
            "pos_y": -544,
            "layout_config":[
                {
                    "align_x": "right",
                    "spacing": 0,
                    "cells": [
                        {
                            "type": "image",
                            "text_key": "logo",
                            "height": 100
                        }
                    ]
                },
                {
                    "align_x": "right",
                    "cells": [
                        {
                            "type": "text",
                            "text_key": "防伪",
                            "font_size": 24,
                            "width_ratio": 0.95,
                            "shadow_color": (0, 0, 0, 200),
                            "shadow_offset": (2, 2), 
                            "shadow_blur": 3, 
                            "font_path": "/Users/teacher/Library/Fonts/FZDHTJW.TTF"
                        },
                        {
                            "space_right": -10,
                            "type": "text",
                            "text_key": "sn_code",
                            "shadow_color": (0, 0, 0, 180),
                            "shadow_offset": (2, 2), 
                            "shadow_blur": 3, 
                            "font_size": 26,
                            "font_path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/typopro-ptmono-bold.ttf",
                        }
                    ]
                }

            ]
        }
    ]

    background_path = "/Users/teacher/Desktop/5张/图片.png"
    base_name, ext = os.path.splitext(background_path)
    output_path = f"{base_name}_加水印{ext}"
    
    render_component_to_image(
        background_path=background_path,
        output_path=output_path,
        layout_data=layout_data,
        texts=my_texts,
        common_config=my_common_config,
    )