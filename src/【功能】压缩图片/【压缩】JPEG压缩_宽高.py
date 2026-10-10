from PIL import Image
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

def compress_jpeg(input_path, output_path, quality=75, max_width=1920):
    """
    专为 JPEG 图片设计的压缩函数
    :param quality: 1-100, 推荐 70-85
    :param max_width: 最大宽度，超过则等比缩放
    """
    with Image.open(input_path) as img:
        # 1. 转换为 RGB 模式 (JPEG 不支持透明)
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        
        # 2. 智能缩放 (保持宽高比)
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # 3. 保存并压缩
        img.save(output_path, format='JPEG', quality=quality, optimize=True)
        
        # 打印压缩效果
        original_size = os.path.getsize(input_path) / 1024
        new_size = os.path.getsize(output_path) / 1024
        print(f"✅ {os.path.basename(input_path)}: {original_size:.1f}KB → {new_size:.1f}KB (质量={quality})")

if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/百度网盘下载/2M/扫描_压缩/教学工作1_扫描版__提取的图片"
    quality=30


    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_压缩{ext}"
        compress_jpeg(
            input_path=input_path,
            output_path=output_path,
            quality=quality
        )
    elif os.path.isdir(input_path):
        counter = [0] 
        def callback_func(input_file, output_file):
            counter[0] += 1
            print(f"正在压缩第{counter[0]}张图片")
            compress_jpeg(
                input_path=input_file,
                output_path=output_file,
                quality=quality
            )

        input_dir = input_path
        output_dir = f"{input_dir}_JPEG压缩"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else: 
         print(f"地址无效: {input_path}")