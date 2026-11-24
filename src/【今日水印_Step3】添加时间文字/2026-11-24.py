from create_widget import create_weather_widget_v2


# ================= 测试运行 =================
if __name__ == "__main__":
    
    # 定义 Layer（组件画布）的属性
    my_layer = {
        "width": 1200,   # Layer 宽度
        "height": 550,   # Layer 高度
        "pos_x": 100,    # 贴在背景图的 X 坐标
        "pos_y": -80,     # 贴在背景图的 Y 坐标
        "align": "left", # 文字在 Layer 内的对齐方式
        "spacing": 20,   # 行距
        "layout_padding": 20 # 文字距离 Layer 边缘的留白
    }

    # 如果你想微调某一行
    my_custom_rows = [
        {
            "text": "09:51", 
            "font_size": 280, 
            "text_color": (255, 255, 255, 255),
            "shadow_offset": (5, 5), "shadow_blur": 4, "texture_mask": True
        },
        {
            "text": "2026-11-20  星期五  阴  15℃",
            "font_size": 80, 
            "text_color": (200, 200, 200, 255) # 稍微变灰一点
        },
        {
            "text": "漳州市龙海区·福建华夏高级技工学校(龙江校区)",
            "font_size": 60,
            "font_path": "simhei.ttf" # 单独指定黑体
        }
    ]

    create_weather_widget_v2(
        input_image_path="/Volumes/西数4T外置/Chrome下载目录/美图设计室_11_24_2026/001_output2/02.jpg", # 换成 "bg.jpg" 即可
        output_image_path="layer_output.png",
        date_str="2026-11-20",
        time_str="09:51",
        weather_str="阴",
        temp_str="15℃",
        location_str="漳州市龙海区·福建华夏高级技工学校(龙江校区)",
        layer_config=my_layer,
        rows_config=my_custom_rows
    )