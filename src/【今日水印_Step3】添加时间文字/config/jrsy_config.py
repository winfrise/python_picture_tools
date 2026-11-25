# ✨ 公共配置（相当于 CSS 的 body 选择器）
common_config = {
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
        "pos_y": -44,
        "scale": 1,
        "standard_width": 2160,
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
                            "path": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/【今日水印_Step3】添加时间文字/assets/111.png", 
                            "pos": (100, 0),                # 蒙版相对文字左上角的偏移，默认 (0, 0)
                            "scale_width": 0.3,           # 宽度缩放比例，默认 1.0
                            "scale_height": 0.3,          # 高度缩放比例，默认 1.0
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
        "pos_y": -44,
        "scale": 1,
        "standard_width": 2160,
        "layout_config":[
            {
                "align_x": "right",
                "spacing": 0,
                "cells": [
                    {
                        "type": "image",
                        "text_key": "logo",
                        "width": 210
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
                        "space_right": 10,
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
