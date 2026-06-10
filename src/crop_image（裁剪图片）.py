from PIL import Image

def crop_image(image_path, crop_params, output_path):
    """
    根据给定的坐标参数裁剪图片并保存。
    
    :param image_path: str, 原始图片的地址路径
    :param crop_params: dict, 包含 top, bottom, left, right 的字典
    :param output_path: str, 裁剪后图片的输出保存路径
    """
    # 1. 打开图片
    img = Image.open(image_path)
    
    # 2. 从字典中提取参数，并按 Pillow 要求的顺序组装为元组 (left, upper, right, lower)
    bbox = (crop_params['left'], crop_params['top'], crop_params['right'], crop_params['bottom'])
    
    # 3. 执行裁剪操作
    cropped_img = img.crop(bbox)
    
    # 4. 保存裁剪后的图片
    cropped_img.save(output_path)
    
    print(f"图片已成功裁剪并保存至: {output_path}")

# --- 测试调用示例 ---
if __name__ == "__main__":
    input_image = "input.jpg"
    output_image = "output.jpg"
    
    # 定义裁剪区域参数
    params = {
        "top": 100,
        "bottom": 400,
        "left": 100,
        "right": 400
    }
    
    crop_image(input_image, params, output_image)