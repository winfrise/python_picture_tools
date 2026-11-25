from create_widget import batch_process_folder
from datetime import datetime
import os
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
        "sn_code": "KTHAN1E3Y3X3BP",
        "防伪": "防伪码" # ⚠️ 你的原代码里似乎漏了这个 key，这里补上
    }

    # ✨ 修改这里：输入文件夹 和 输出文件夹
    input_directory = "/Users/teacher/Desktop/5张" 
    output_directory = "/Users/teacher/Desktop/5张_加水印" 
    
    # 执行批量处理
    batch_process_folder(
        input_dir=input_directory,
        output_dir=output_directory,
        layout_data=layout_data,
        texts=my_texts,
        common_config=common_config,
    )