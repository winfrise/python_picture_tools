import os
from PIL import Image

def process_image(input_path, output_path, quality=85, max_size=None, dpi=None):
    """
    处理单张图片：转换模式、缩放、保存
    """
    try:
        with Image.open(input_path) as img:
            # --- 1. 模式转换 (修复 RGBA 报错) ---
            if img.mode in ("RGBA", "P"):
                # 创建白色背景
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[3]) # 使用 alpha 通道作为 mask
                else:
                    background.paste(img)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # --- 2. 同比例缩放 (如果设置了 max_size) ---
            if max_size:
                # thumbnail 会原地修改图片，且保持长宽比
                img.thumbnail(max_size, Image.LANCZOS)

            # --- 3. 保存配置 ---
            save_kwargs = {"quality": quality, "optimize": True}
            
            # 设置分辨率 (DPI)
            if dpi:
                save_kwargs["dpi"] = (dpi, dpi)
            
            # 针对 PNG 的特殊处理
            if output_path.lower().endswith('.png'):
                save_kwargs.pop("quality", None)
                save_kwargs["compress_level"] = 6 # PNG 使用 compress_level (0-9)

            img.save(output_path, **save_kwargs)
            return True, f"成功处理: {os.path.basename(input_path)} -> 尺寸: {img.size}"
    except Exception as e:
        return False, f"处理失败 {os.path.basename(input_path)}: {e}"

def compress_images(input_dir, output_dir, quality=85, max_size=None, dpi=None):
    """
    批量压缩、缩放及设置分辨率工具 (文件夹处理)
    """
    if not os.path.exists(input_dir):
        print(f"错误：输入目录不存在 -> {input_dir}")
        return 0

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录：{output_dir}")

    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    count = 0

    print(f"开始处理目录... [质量: {quality}, 最大尺寸: {max_size}, DPI: {dpi}]")
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_formats):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            success, msg = process_image(input_path, output_path, quality, max_size, dpi)
            print(msg)
            if success:
                count += 1

    return count

def process_single_file(input_file, output_file, quality=85, max_size=None, dpi=None):
    """
    处理单个文件
    """
    if not os.path.exists(input_file):
        print(f"错误：输入文件不存在 -> {input_file}")
        return 0

    # 确保输出文件的目录存在
    if output_file == None:
        base_name, ext = os.path.splitext(input_file)
        output_file = f"{base_name}_output{ext}"

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    success, msg = process_image(input_file, output_file, quality, max_size, dpi)
    print(msg)
    return 1 if success else 0

if __name__ == "__main__":

    input_path = "/Users/teacher/Desktop/111"   # 可以是文件路径或文件夹路径
    output_path = "/Users/teacher/Desktop/1112" # 对应的输出文件或文件夹路径
    quality = 30
    max_size = (700, 1754)
    dpi = 72

    # 判断输入是文件还是目录
    if os.path.isfile(input_path):
        count = process_single_file(
            input_file = input_path, 
            output_file = None, 
            quality = quality, 
            max_size = max_size, 
            dpi = dpi
        )
        print(f"\n单文件处理完成。")
    elif os.path.isdir(input_path):
        count = compress_images(input_path, output_path, quality, max_size, dpi)
        print(f"\n处理完成！共处理 {count} 张图片。")
    else:
        print(f"错误：输入路径既不是文件也不是目录 -> {input_path}")

# A4大小
# 屏幕显示/网页通用标准 (72 DPI)
# 宽：595 像素
# 高：842 像素
# 普通打印/文档标准 (96 DPI)
# 宽：794 像素
# 高：1123 像素
# 高清印刷/高质量出版标准 (300 DPI)
# 宽：2480 像素
# 高：3508 像素
    