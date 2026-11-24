from overlay_image import add_images_to_single, add_images_to_batch
import os

image_list = [
    # 左上角 (0, 0) 开始
    {
        "path": "/Users/teacher/Desktop/jinrishuiyin.png", 
        "x": -1, "y": -1
    },

    # # 距右边 50 像素, 距上边 200 像素
    # {"path": "watermark.png", "x": -50, "y": 200},

    # # 距左下角 30, 40 像素
    # {"path": "stamp.png", "x": 30, "y": -40},

    # # 指定 patch 显示尺寸
    # {"path": "tag.png", "x": -20, "y": -20, "width": 300, "height": 120},
]


# base_size = (2304, 4096)
base_size = (2311, 1733) # 只指定高度，宽度按比例自动

# input_image = "/Users/teacher/Desktop/5张/01.png"
# base_name, ext = os.path.splitext(input_image)
# output_image = f"{base_name}_output{ext}"
# add_images_to_single(
#     input_image = input_image, 
#     output_image = output_image, 
#     image_list = image_list, 
#     base_size=base_size
# )

# 批量处理
input_dir = "/Volumes/西数4T外置/Chrome下载目录/美图设计室_11_24_2026/001"
output_dir = f"{input_dir}_output"
add_images_to_batch(
    input_dir=input_dir,
    output_dir=output_dir,
    image_list=image_list,
    base_size=base_size,
)