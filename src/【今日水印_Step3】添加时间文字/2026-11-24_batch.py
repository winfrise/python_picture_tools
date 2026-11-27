from create_widget import batch_process_folder
from datetime import datetime
import os
import copy
from config.jrsy_config import common_config,layout_data
from tools.generate_security_code import generate_security_code

if __name__ == "__main__":

    def get_week(d):
        try: return ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][datetime.strptime(d, "%Y-%m-%d").weekday()]
        except: return "未知"

    date_val = "2026-11-08"
    my_texts = {
        "time": "09:56",
        "date": date_val,
        "weather": "阴",
        "temp": "6℃",
        "week": lambda: get_week(date_val),
        "weather_line": "{week} {weather} {temp}",
        "location": "大连市甘井子区·长安凯程(东升汽车大连东瑞店)",
        "logo": "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/【今日水印_Step3】添加时间文字/assets/jr_logo.png",
        "sn_code": generate_security_code,
        "防伪": "防伪" # ⚠️ 你的原代码里似乎漏了这个 key，这里补上
    }

    my_layout_data = copy.deepcopy(layout_data)
    standard_width = 2160
    layer_data = [
        {
            "pos_x":44,
            "pos_y": -44,
            "scale": 1.2,
            "standard_width": standard_width
        },
        {
            "pos_x": -44,
            "pos_y": -24,
            "scale": 1.2,
            "standard_width": standard_width
        }
    ]

    my_layout_data[0].update(layer_data[0]) 
    my_layout_data[1].update(layer_data[1]) 


    # ✨ 修改这里：输入文件夹 和 输出文件夹
    input_directory = "/Users/teacher/Desktop/未命名文件夹/001" 
    output_directory = f"{input_directory}_加水印"
    temp_work_dir = f"{input_directory}_temp"
    
    # 执行批量处理
    batch_process_folder(
        input_dir=input_directory,
        output_dir=output_directory,
        layout_data=my_layout_data,
        texts=my_texts,
        common_config=common_config,
        temp_work_dir=temp_work_dir
    )