import os
from PIL import Image

def luban_compress(input_path, output_path, target_size_kb=100):

    if output_path is None:
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_鲁班压缩{ext}"

    """
    鲁班压缩算法：自适应尺寸 + 二分搜索质量
    """
    img = Image.open(input_path)
    
    # 1. 格式智能选择与元数据净化
    if img.format == 'PNG' and img.mode != 'RGBA':
        img = img.convert('RGB')
        # 如果原图是PNG且无透明通道，输出改为JPG以获得更好压缩率
        if not output_path.lower().endswith('.jpg') and not output_path.lower().endswith('.jpeg'):
            output_path = os.path.splitext(output_path)[0] + '.jpg'

    # 2. 尺寸预判与自适应缩放
    long_side = max(img.size)
    if long_side > 1664:
        scale = long_side / 1664
        new_size = (int(img.size[0] / scale), int(img.size[1] / scale))
        img = img.resize(new_size, Image.LANCZOS)

    # 3. 多轮质量试探与二分搜索
    left, right = 10, 95
    best_quality = 85
    
    # 【修复点】：生成临时文件时，保留原始后缀，只加前缀或中间标识
    # 例如：output.jpg -> output_test.jpg
    base, ext = os.path.splitext(output_path)
    temp_path = f"{base}_test{ext}" 
    
    while left <= right:
        mid = (left + right) // 2
        
        save_kwargs = {'optimize': True}
        
        # 根据后缀决定保存参数
        if ext.lower() in ['.jpg', '.jpeg']:
            save_kwargs['quality'] = mid
            save_kwargs['format'] = 'JPEG' # 显式指定格式更稳妥
        elif ext.lower() == '.png':
            save_kwargs['compress_level'] = 6 # PNG的质量参数逻辑不同，这里简化处理
            save_kwargs['format'] = 'PNG'
            
        try:
            img.save(temp_path, **save_kwargs)
            
            current_size_kb = os.path.getsize(temp_path) / 1024
            
            if current_size_kb <= target_size_kb:
                best_quality = mid
                left = mid + 1 
            else:
                right = mid - 1 
        except Exception as e:
            print(f"保存临时文件出错: {e}")
            break

    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # 4. 最终保存并剥离元数据
    final_kwargs = {'optimize': True}
    if ext.lower() in ['.jpg', '.jpeg']:
        final_kwargs['quality'] = best_quality
        final_kwargs['exif'] = b''  # 剥离EXIF
        final_kwargs['format'] = 'JPEG'
    elif ext.lower() == '.png':
        final_kwargs['compress_level'] = 9
        final_kwargs['format'] = 'PNG'
        
    img.save(output_path, **final_kwargs)
    print(f"[鲁班压缩] 完成: {output_path} | 最优质量参数: {best_quality}")

if __name__ == "__main__":
    # 鲁班压缩：将图片压缩到 150KB 以内
    input_path = "/Users/teacher/Desktop/未命名文件夹 2/page1_img1.jpeg"
    output_path = None
    target_size_kb = 50

    luban_compress(
        input_path=input_path,
        output_path=output_path,
        target_size_kb=target_size_kb
    )