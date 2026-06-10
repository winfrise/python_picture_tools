from PIL import Image

def crop_by_margins(image_path, crop_params, output_path):
    """
    根据四周边缘的裁剪厚度来裁剪图片并保存。
    
    :param image_path: str, 原始图片的地址路径
    :param crop_params: dict, 包含需要从四边裁剪掉的宽度/高度 {top, bottom, left, right}
    :param output_path: str, 处理后图片的输出保存路径
    """
    # 1. 打开原图并获取尺寸
    original_img = Image.open(image_path)
    width, height = original_img.size
    
    # 2. 提取参数
    margin_left = crop_params['left']
    margin_top = crop_params['top']
    margin_right = crop_params['right']
    margin_bottom = crop_params['bottom']
    
    # 3. 计算保留区域的绝对坐标 (left, upper, right, lower)
    bbox = (
        margin_left,                       # 左边界：向右偏移
        margin_top,                        # 上边界：向下偏移
        width - margin_right,              # 右边界：总宽度减去右侧裁剪厚度
        height - margin_bottom             # 下边界：总高度减去底部裁剪厚度
    )
    
    # 4. 执行裁剪操作
    cropped_img = original_img.crop(bbox)
    
    # 5. 保存处理后的图片
    cropped_img.save(output_path)
    print(f"已成功按边距裁剪图片，并保存至: {output_path}")


# --- 测试调用示例 ---
if __name__ == "__main__":
    input_file = "/Users/teacher/Desktop/《临床基础检验技术》复习要点/《临床基础检验技术》复习要点_extracted_images/page1_img1.jpeg"
    output_file = "/Users/teacher/Desktop/《临床基础检验技术》复习要点/《临床基础检验技术》复习要点_extracted_images/page1_img1111111.jpeg"
    params = {
        "top": 50,      # 从顶部裁剪掉 50px 的高度
        "bottom": 50,   # 从底部裁剪掉 50px 的高度
        "left": 100,    # 从左侧裁剪掉 100px 的宽度
        "right": 100    # 从右侧裁剪掉 100px 的宽度
    }
    
    crop_by_margins(image_path = input_file, crop_params = params, output_path = output_file)