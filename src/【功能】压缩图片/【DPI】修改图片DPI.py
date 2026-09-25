from PIL import Image
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import batch_process_file_with_callback

def change_image_dpi(input_path, output_path, dpi=300):
    """
    修改图片的 DPI
    :param input_path: 原图片路径
    :param output_path: 保存的新图片路径
    :param dpi: 目标 DPI，默认 300
    """
    try:
        img = Image.open(input_path)
        
        # 获取图片格式，如果无法获取则默认使用 PNG
        image_format = img.format if img.format else 'PNG'
        
        # 保存时通过 dpi 参数指定新的 DPI
        # 注意：JPEG 格式不支持透明通道，如果原图是 RGBA 需要转换
        if image_format == 'JPEG' and img.mode == 'RGBA':
            img = img.convert('RGB')
            
        img.save(output_path, format=image_format, dpi=(dpi, dpi))
        print(f"✅ 成功: {input_path} -> DPI 已修改为 {dpi}，保存至: {output_path}")
        
    except Exception as e:
        print(f"❌ 失败: {input_path}，错误信息: {e}")

# --- 使用示例 ---
if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/百度网盘下载/未命名文件夹 2/0925绿顶青山计划书__合成的图片_DPI_300"
    dpi = 72
    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{input_path}_output_转DPI{dpi}{ext}"
        change_image_dpi(
            input_path = input_path, 
            output_path = output_path, 
            dpi=dpi
        )
    elif os.path.isdir(input_path):
        # 批量处理
        input_dir = input_path
        output_dir = f"{input_dir}_output_转DPI{dpi}"
        
        def callback_func(input_file, output_file):
            change_image_dpi(
                input_path = input_file, 
                output_path = output_file, 
                dpi=dpi
            )
        batch_process_file_with_callback(
            input_dir = input_dir,
            output_dir= output_dir,
            callback_func=callback_func
        )
    # 修改单张图片
