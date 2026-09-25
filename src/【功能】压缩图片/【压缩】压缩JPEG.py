from PIL import Image
import os

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

# 使用示例
compress_jpeg("photo.jpg", "photo_compressed.jpg", quality=75)