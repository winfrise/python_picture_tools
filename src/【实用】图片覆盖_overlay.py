from PIL import Image
from typing import List, Callable, Union
import os
import re
from utils import batch_process_file_with_callback

def overlay_images(
    bg_image_path: str, 
    get_overlay_list_func: Callable[[str], List[str]], 
    save_path: str = None,
    position: tuple = (0, 0),
    resize_to_bg: bool = False
) -> Image.Image:
    """
    将一组图片覆盖到背景图上
    
    :param bg_image_path: 背景图片的本地路径
    :param get_overlay_list_func: 获取覆盖图片列表的函数，入参为图片地址，返回图片路径列表
    :param save_path: 可选，合并后图片的保存路径
    :param position: 覆盖图片在背景图上的起始坐标 (x, y)，默认为左上角 (0, 0)
    :param resize_to_bg: 是否将覆盖图片缩放至与背景图相同大小，默认为 False
    :return: 合并后的 PIL.Image 对象
    """
    # 1. 打开背景图并转换为 RGBA 模式（支持透明度）
    if not os.path.exists(bg_image_path):
        raise FileNotFoundError(f"背景图片未找到: {bg_image_path}")
        
    background = Image.open(bg_image_path).convert("RGBA")
    
    # 2. 调用传入的函数，获取需要覆盖的图片列表
    overlay_list = get_overlay_list_func(bg_image_path)
    
    if not isinstance(overlay_list, list):
        raise TypeError("get_overlay_list_func 必须返回一个包含图片路径的列表")

    # 3. 遍历图片列表，依次覆盖
    for overlay_path in overlay_list:
        if not os.path.exists(overlay_path):
            print(f"警告: 覆盖图片未找到，已跳过 -> {overlay_path}")
            continue
            
        overlay = Image.open(overlay_path).convert("RGBA")
        
        # 如果需要，将覆盖图缩放到与背景图一样大
        if resize_to_bg:
            overlay = overlay.resize(background.size, Image.Resampling.LANCZOS)
            
        # 使用 paste 进行覆盖，第三个参数是 mask，用于处理透明通道
        background.paste(overlay, position, overlay)
        
    # 4. 保存或返回结果
    if save_path:
        # 如果保存为 JPG，需要去掉 Alpha 通道
        if save_path.lower().endswith(('.jpg', '.jpeg')):
            background = background.convert("RGB")
        background.save(save_path)
        print(f"图片合并完成，已保存至: {save_path}")
        
    return background

# 调用主函数
if __name__ == "__main__":
    # 模拟一个获取图片列表的函数
    def my_custom_get_images(bg_path: str) -> List[str]:
        """
        根据背景图文件名中 'page' 后的数字判断奇偶，返回不同的图片列表
        """
        # 1. 从完整路径中提取纯文件名，例如 'page15_img1.jpeg'
        filename = os.path.basename(bg_path)
        
        # 2. 使用正则表达式提取 'page' 后面的数字
        # 匹配模式：'page' 后面紧跟的连续数字
        match = re.search(r'page(\d+)', filename)
        # 默认返回空列表（如果没找到数字）
        overlay_list = []
        
        if match:
            page_num = int(match.group(1))  # 提取到的数字，例如 15

            print(f"识别到文件名: {filename}, 提取数字: {page_num}")
            if 7 <= page_num <= 41:
                # 3. 判断奇偶并返回对应的图片路径
                if page_num % 2 != 0:
                    # 奇数返回图片1
                    overlay_list = ["/Users/teacher/Desktop/20260830/改公司名称100元/overlay_1.png"] 
                else:
                    # 偶数返回图片2
                    overlay_list = ["/Users/teacher/Desktop/20260830/改公司名称100元/overlay_2.png"]
        else:
            print(f"警告: 文件名 '{filename}' 中未找到 'page' 及数字")
            
        return overlay_list


    image_path = "/Users/teacher/Desktop/20260830/改公司名称100元/修改过的图片"
    if os.path.isfile(image_path):
        bg_image_path = image_path
        base_name, ext = os.path.splitext(bg_image_path)
        save_path = f"{base_name}_output_图片覆盖{ext}"
        overlay_images(
            bg_image_path=bg_image_path,
            get_overlay_list_func=my_custom_get_images,
            save_path=save_path,
            position=(0, 0),       # 从坐标 (50, 50) 开始覆盖
            resize_to_bg=False       # 保持覆盖图原始大小
        )
    elif os.path.isdir(image_path):
        def callback_func(input_file, output_file):
            overlay_images(
                bg_image_path=input_file,
                get_overlay_list_func=my_custom_get_images,
                save_path=output_file,
                position=(0, 0),       # 从坐标 (50, 50) 开始覆盖
                resize_to_bg=False       # 保持覆盖图原始大小
            )
        input_dir = image_path
        output_dir = f'{input_dir}_output_图片覆盖'
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效")