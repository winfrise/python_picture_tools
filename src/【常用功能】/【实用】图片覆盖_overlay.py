from PIL import Image
from typing import List, Callable, Union
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from utils import batch_process_file_with_callback

def overlay_images(
    image_path: str, 
    overlay_image_path: Callable[[str], List[str]], 
    save_path: str = None,
) -> Image.Image:
    """
    将一组图片覆盖到背景图上
    
    :param bg_image_path: 背景图片的本地路径
    :param overlay_image_func: 获取覆盖图片列表的函数，入参为图片地址，返回图片路径列表
    :param save_path: 可选，合并后图片的保存路径
    :param position: 覆盖图片在背景图上的起始坐标 (x, y)，默认为左上角 (0, 0)
    :param resize_to_bg: 是否将覆盖图片缩放至与背景图相同大小，默认为 False
    :return: 合并后的 PIL.Image 对象
    """
    # 1. 打开背景图并转换为 RGBA 模式（支持透明度）
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"背景图片未找到: {image_path}")
        
    image = Image.open(image_path).convert("RGBA")
    

    if callable(overlay_image_path):
        overlay_image_path = overlay_image_path(image_path, image)
    
    if not overlay_image_path:
        raise TypeError("overlay_image_path 不能为空")

    if not os.path.exists(overlay_image_path):
        print(f"警告: 覆盖图片未找到，已跳过 -> {overlay_image_path}")
        
    overlay_image = Image.open(overlay_image_path).convert("RGBA")
    
        
    # 使用 paste 进行覆盖，第三个参数是 mask，用于处理透明通道
    image.paste(overlay_image, (0, 0), overlay_image)
        
    # 4. 保存或返回结果
    if save_path:
        # 如果保存为 JPG，需要去掉 Alpha 通道
        if save_path.lower().endswith(('.jpg', '.jpeg')):
            image = image.convert("RGB")
        image.save(save_path)
        print(f"图片合并完成，已保存至: {save_path}")
        
    return image

# 调用主函数
if __name__ == "__main__":
    # 模拟一个获取图片列表的函数
    def custom_overlay_image_func(image_path, image):
        # 1. 从完整路径中提取纯文件名，例如 'page15_img1.jpeg'
        # filename = os.path.basename(image_path)
        # page_num = int(m.group(1)) if (m := re.search(r'page(\d+)', filename)) else None

        width, height = image.size
        if (width > height):
            return  "/Users/teacher/Desktop/百度网盘下载/50+10元/mask_h.png"

        return "/Users/teacher/Desktop/百度网盘下载/50+10元/mask_v.png"



    image_path = "/Users/teacher/Desktop/百度网盘下载/50+10元/尺木酒店设计方案(1)__提取的图片/001"
    custom_overlay_image = "/Users/teacher/Desktop/企业画册/mask_right.png"

    overlay_image_path = custom_overlay_image_func

    if os.path.isfile(image_path):
        bg_image_path = image_path
        base_name, ext = os.path.splitext(bg_image_path)
        save_path = f"{base_name}_output_图片覆盖{ext}"
        overlay_images(
            image_path=bg_image_path,
            overlay_image_path=overlay_image_path,
            save_path=save_path,
        )
    elif os.path.isdir(image_path):
        def callback_func(input_file, output_file):
            overlay_images(
                image_path=input_file,
                overlay_image_path=overlay_image_path,
                save_path=output_file,
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