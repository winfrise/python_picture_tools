from create_widget import render_component_to_image
from datetime import datetime
import os
import copy
from config.jrsy_config import common_config,layout_data

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
        "logo": "/Users/teacher/Desktop/今日水印_2.png",
        "sn_code": "KTHAN1E3Y3X3BP"
    }


    my_layout_data = copy.deepcopy(layout_data)
    standard_width = 2160
    layer_data = [
        {
            "pos_x":44,
            "pos_y": -44,
            "scale": None,
            "standard_width": standard_width
        },
        {
            "pos_x": -44,
            "pos_y": -24,
            "scale": None,
            "standard_width": standard_width
        }
    ]

    my_layout_data[0].update(layer_data[0]) 
    my_layout_data[1].update(layer_data[1]) 

    background_path = "/Users/teacher/Desktop/未命名文件夹/2.jpeg"
    base_name, ext = os.path.splitext(background_path)
    output_path = f"{base_name}_加水印{ext}"
    
    render_component_to_image(
        background_path=background_path,
        output_path=output_path,
        layout_data=layout_data,
        texts=my_texts,
        common_config=common_config,
    )