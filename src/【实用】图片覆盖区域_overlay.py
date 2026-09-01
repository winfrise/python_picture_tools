from PIL import Image
import os
from utils import batch_process_file_with_callback

def overlay_image(background_path, overlay_path, output_path, position=(0, 0), overlay_size=None):
    """
    将一张图片覆盖到另一张图片上（默认左上角对齐）
    
    :param background_path: 背景图片路径
    :param overlay_path: 覆盖图片路径（支持透明背景，如 PNG）
    :param output_path: 输出图片路径
    :param position: 覆盖图片左上角的坐标 (x, y)，默认为 (0, 0) 即左上角
    :param overlay_size: 覆盖图片的目标尺寸 (width, height)，默认为 None 表示保持原大小
    """
    # 1. 打开背景图并转换为 RGBA 模式（支持透明通道）
    background = Image.open(background_path).convert("RGBA")
    
    # 2. 打开覆盖图并转换为 RGBA 模式
    overlay = Image.open(overlay_path).convert("RGBA")
    
    # 3. 如果需要调整覆盖图的大小
    if overlay_size:
        overlay = overlay.resize(overlay_size, Image.Resampling.LANCZOS)
        
    # 4. 创建一个与背景图一样大的透明图层
    # 这一步是为了防止覆盖图超出背景图边界导致报错
    temp_image = Image.new("RGBA", background.size)
    
    # 5. 将覆盖图粘贴到透明图层的指定位置
    # 因为 position 默认是 (0, 0)，所以这里默认就是左上角
    temp_image.paste(overlay, position)
    
    # 6. 使用 alpha_composite 将透明图层合成到背景图上
    # 注意：alpha_composite 能完美处理 PNG 的半透明效果
    result = Image.alpha_composite(background, temp_image)
    
    # 7. 保存结果（如果需要保存为 JPG，需转回 RGB）
    if output_path.lower().endswith(('.jpg', '.jpeg')):
        result = result.convert("RGB")
        
    result.save(output_path)
    print(f"✅ 图片合成成功！已保存至: {output_path}")

# --- 使用示例 ---
if __name__ == "__main__":
    # 这里使用了你文档中的路径示例
    image_path = "/Users/teacher/Desktop/20260830/项目图片去水印定200/111/证书/分类2"
    overlay_path = "/Users/teacher/Desktop/20260830/项目图片去水印定200/111/证书/test/overlay.png"

    if os.path.isfile(image_path):
        base_name, ext = os.path.splitext(image_path)
        output_path=f"{base_name}_output_覆盖区域{ext}"
        overlay_image(
            background_path=image_path, 
            overlay_path=overlay_path, 
            output_path=output_path,
        )
    elif os.path.isdir(image_path):
        def callback_func(input_file, output_file):
            overlay_image(
                background_path=input_file, 
                overlay_path=overlay_path, 
                output_path=output_file,
            )
        input_dir = image_path
        output_dir = f'{image_path}_output_覆盖区域'
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效")