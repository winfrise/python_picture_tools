import os, sys
import subprocess
from PIL import Image
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

def find_best_quality(img, temp_path, target_size_kb):
    """
    辅助函数：二分搜索最佳质量参数
    """
    left, right = 1, 95
    best_q = 1  # 初始化为下界，防止连 quality=1 都超标时返回默认值
    
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
            print(f"[Pipeline] 保存临时文件出错: {e}")
            break
            
    return best_q

def trimage_lossless_optimize(file_path):
    """
    调用底层命令行工具进行严格无损压缩
    """
    ext = os.path.splitext(file_path)[-1].lower()
    try:
        if ext in ['.jpg', '.jpeg']:
            cmd = ['jpegoptim', '--strip-all', '--all-progressive', '-o', file_path]
        elif ext == '.png':
            # -o7: 最高优化级别, -strip all: 剥离元数据
            cmd = ['optipng', '-o7', '-strip', 'all', '-clobber', file_path]
        else:
            return

        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError:
        print("[Pipeline] 警告: 未找到 jpegoptim 或 optipng，跳过 Trimage 无损优化。")
    except subprocess.CalledProcessError as e:
        print(f"[Pipeline] Trimage 优化失败: {e.stderr.decode()}")

def compress_pipeline(input_path, output_path, target_size_kb=50):

    if output_path is None:
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_串联压缩{ext}"

    """
    终极压缩流水线：鲁班策略(定尺寸+质量) -> Trimage(无损精修)
    """
    img = Image.open(input_path)
    
    # 1. 格式智能选择与元数据净化
    if img.format == 'PNG' and img.mode != 'RGBA':
        img = img.convert('RGB')
        if not output_path.lower().endswith(('.jpg', '.jpeg')):
            output_path = os.path.splitext(output_path)[0] + '.jpg'

    # 2. 鲁班策略：循环尝试，直到体积达标或尺寸无法再缩
    min_dimension = 100 
    temp_path = f"{os.path.splitext(output_path)[0]}_test{os.path.splitext(output_path)[1]}"
    
    while True:
        current_width, current_height = img.size
        
        # 阶段 A: 在当前尺寸下寻找最优质量
        best_quality = find_best_quality(img, temp_path, target_size_kb)
        
        # 检查当前最佳质量下的文件大小
        img.save(temp_path, quality=best_quality, optimize=True)
        actual_size_kb = os.path.getsize(temp_path) / 1024
        
        # 如果达标，或者尺寸已经很小了，直接保存并退出循环
        if actual_size_kb <= target_size_kb or current_width <= min_dimension:
            final_kwargs = {'quality': best_quality, 'optimize': True}
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                final_kwargs['exif'] = b'' 
            img.save(output_path, **final_kwargs)
            print(f"[Pipeline-鲁班] 达标: {output_path} | 大小: {actual_size_kb:.1f}KB | 质量: {best_quality} | 尺寸: {img.size}")
            break

        # 阶段 B: 如果依然超标，强制缩小尺寸 (每次缩小 20%)
        # print(f"[Pipeline-鲁班] 警告: 质量降至最低仍为 {actual_size_kb:.1f}KB，正在缩小尺寸...")
        # scale_factor = 0.8
        # new_size = (int(current_width * scale_factor), int(current_height * scale_factor))
        # img = img.resize(new_size, Image.LANCZOS)

    # 清理临时文件
    if os.path.exists(temp_path): os.remove(temp_path)

    # 3. Trimage 无损精修：在达标基础上继续榨干冗余字节
    trimage_lossless_optimize(output_path)
    
    # 打印最终结果
    final_size_kb = os.path.getsize(output_path) / 1024
    print(f"[Pipeline-最终] 压缩完成: {output_path} | 最终大小: {final_size_kb:.1f}KB")

if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/百度网盘下载/2M/（已压缩）郑州市课题_扫描版__提取的图片"
    
    # target_size_kb = 50

    total_size_kb = 2 * 1024-500
    total_page = 34
    target_size_kb = math.floor(total_size_kb / total_page)
    print(f"target_size_kb: {target_size_kb}")

    if os.path.isfile(input_path):
        output_path = None
        compress_pipeline(
            input_path=input_path,
            output_path=output_path,
            target_size_kb=target_size_kb,
        )
    elif os.path.isdir(input_path):
        counter = [0] 
        def callback_func(input_file, output_file):
            counter[0] += 1
            print(f"正在压缩第{counter[0]}张图片")
            compress_pipeline(
                input_path=input_file,
                output_path=output_file,
                target_size_kb=target_size_kb,
            )

        input_dir = input_path
        output_dir = f"{input_dir}_串联压缩"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else: 
         print(f"地址无效: {input_path}")