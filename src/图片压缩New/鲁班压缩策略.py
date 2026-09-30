import os
from PIL import Image

def luban_compress(input_path, output_path, target_size_kb=50):

    if output_path is None:
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_鲁班压缩11{ext}"


    """
    鲁班压缩算法（修复版）：支持自动缩放以达成目标体积
    """
    img = Image.open(input_path)
    
    # 1. 格式智能选择与元数据净化
    # 如果原图是PNG且无透明通道，转为JPG更容易达到小体积
    if img.format == 'PNG' and img.mode != 'RGBA':
        img = img.convert('RGB')
        if not output_path.lower().endswith(('.jpg', '.jpeg')):
            output_path = os.path.splitext(output_path)[0] + '.jpg'

    # 2. 核心逻辑：循环尝试，直到体积达标或尺寸无法再缩
    # 设置一个最小尺寸限制，防止缩成蚂蚁图
    min_dimension = 100 
    
    while True:
        current_width, current_height = img.size
        
        # --- 阶段 A: 在当前尺寸下寻找最优质量 ---
        best_quality = find_best_quality(img, output_path, target_size_kb)
        
        # 检查当前最佳质量下的文件大小
        temp_path = f"{os.path.splitext(output_path)[0]}_check.jpg"
        img.save(temp_path, quality=best_quality, optimize=True)
        actual_size_kb = os.path.getsize(temp_path) / 1024
        
        # 如果达标，或者尺寸已经很小了，直接保存并退出
        if actual_size_kb <= target_size_kb or current_width <= min_dimension:
            # 最终保存
            final_kwargs = {'quality': best_quality, 'optimize': True}
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                final_kwargs['exif'] = b'' 
            img.save(output_path, **final_kwargs)
            print(f"[鲁班压缩] 成功: {output_path} | 大小: {actual_size_kb:.1f}KB | 质量: {best_quality} | 尺寸: {img.size}")
            if os.path.exists(temp_path): os.remove(temp_path)
            return

        # --- 阶段 B: 如果依然超标，强制缩小尺寸 (每次缩小 20%) ---
        print(f"[鲁班压缩] 警告: 质量降至最低仍为 {actual_size_kb:.1f}KB，正在缩小尺寸...")
        scale_factor = 0.8
        new_size = (int(current_width * scale_factor), int(current_height * scale_factor))
        img = img.resize(new_size, Image.LANCZOS)
        
        if os.path.exists(temp_path): os.remove(temp_path)

def find_best_quality(img, output_path, target_size_kb):
    """
    辅助函数：二分搜索最佳质量参数
    """
    left, right = 1, 95  # 范围扩大到 1
    best_q = 10
    
    base, ext = os.path.splitext(output_path)
    temp_path = f"{base}_test{ext}"

    while left <= right:
        mid = (left + right) // 2
        try:
            img.save(temp_path, quality=mid, optimize=True)
            size = os.path.getsize(temp_path) / 1024
            
            if size <= target_size_kb:
                best_q = mid
                left = mid + 1  # 尝试更高画质
            else:
                right = mid - 1 # 降低画质
        except Exception as e:
            print(f"保存临时文件出错: {e}")
            break
            
    if os.path.exists(temp_path): os.remove(temp_path)
    return best_q

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