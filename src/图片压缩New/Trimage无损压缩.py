import subprocess
import os

def trimage_compress(input_path, output_path=None):
    """
    Trimage无损压缩：调用底层命令行工具进行严格无损压缩
    :param input_path: 输入图片路径
    :param output_path: 输出图片路径（若为None则原地覆盖）
    """
    if output_path is None:
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_无损压缩{ext}"

    ext = os.path.splitext(input_path)[-1].lower()
    
    try:
        if ext in ['.jpg', '.jpeg']:
            # 严格无损模式：优化Huffman表、渐进式扫描、剥离所有元数据
            cmd = [
                'jpegoptim', 
                '--strip-all', 
                '--all-progressive', 
                '-o',  # 无损优化
                output_path
            ]
        elif ext == '.png':
            # 多轮试探性无损压缩，不改变像素值和调色板
            cmd = [
                'optipng', 
                '-o7',  # 最高优化级别
                '-strip', 'all', 
                '-clobber', 
                '-out', output_path, 
                input_path
            ]
        else:
            print(f"[Trimage] 警告：不支持的格式 {ext}，已跳过。")
            return

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[Trimage] 无损优化完成: {output_path}")
        
    except FileNotFoundError:
        print("[Trimage] 错误：未找到 jpegoptim 或 optipng，请先在系统中安装。")
    except subprocess.CalledProcessError as e:
        print(f"[Trimage] 压缩失败: {e.stderr.decode()}")



if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/未命名文件夹 2/page1_img1.jpeg"
    output_path = None
    
    # Trimage 无损压缩：原地覆盖优化
    trimage_compress(
        input_path=input_path,
        output_path=output_path,
    )