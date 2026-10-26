from PIL import Image
from PIL.ExifTags import TAGS
import os

def get_image_info(image_path):
    """获取图片的基本信息"""
    if not os.path.exists(image_path):
        print(f"文件不存在: {image_path}")
        return None
    
    info = {}
    
    with Image.open(image_path) as img:
        # 基本信息
        info['文件名'] = os.path.basename(image_path)
        info['格式'] = img.format
        info['尺寸'] = img.size  # (宽, 高)
        info['模式'] = img.mode
        info['文件大小'] = f"{os.path.getsize(image_path) / 1024:.2f} KB"
        
        # EXIF 信息
        exif_data = img.getexif()
        if exif_data:
            exif_info = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_info[tag] = value
            info['EXIF'] = exif_info
    
    return info


if __name__ == '__main__':
    result = get_image_info('/Users/teacher/Desktop/1222.jpg')
    for key, value in result.items():
        if key == 'EXIF':
            print(f"{key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"{key}: {value}")