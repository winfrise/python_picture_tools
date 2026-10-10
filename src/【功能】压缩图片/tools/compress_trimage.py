import subprocess
import os, sys
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import batch_process_file_with_callback


def trimage_compress(input_path, output_path=None):
    """
    Trimage无损压缩：调用底层命令行工具进行严格无损压缩
    :param input_path: 输入图片路径
    :param output_path: 输出图片路径（若为None则原地覆盖）
    """
    if output_path is None:
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_无损压缩{ext}"

    # 关键修复1：确保输出目录存在，否则复制/写出会失败
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    ext = os.path.splitext(input_path)[-1].lower()

    try:
        if ext in ['.jpg', '.jpeg']:

            if not os.path.exists(output_path):
                shutil.copyfile(input_path, output_path)

            cmd = [
                'jpegoptim',
                '--strip-all',          # 剥离所有元数据(EXIF/GPS等)
                '--all-progressive',    # 转为渐进式扫描，体积更小
                output_path,            # 原地优化这个已存在的副本
            ]
        elif ext == '.png':
            # optipng 支持 -out 指定输出文件，这个分支原本就是对的，保持不变
            cmd = [
                'optipng',
                '-o7',
                '-strip', 'all',
                '-clobber',
                '-out', output_path,
                input_path,
            ]
        elif ext == '.jpx':
            
            raise ValueError(f"格式{ext}功能待完善")
        else:
            raise ValueError(f"[Trimage] 警告：不支持的格式 {ext}，已跳过。")

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[Trimage] 无损优化完成: {output_path}")

    except FileNotFoundError:
        print("[Trimage] 错误：未找到 jpegoptim 或 optipng，请先在系统中安装。")
    except subprocess.CalledProcessError as e:
        # 关键修复3：打印真实错误，不要再"静默失败"
        print(f"[Trimage] 压缩失败: {e.stderr.decode(errors='ignore')}")


if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/未命名文件夹 2/001/义乌市北遴电子商务商行欧盟授权代表续费（产品组）协议2026.10.20-2027.10.19__提取的图片"

    if os.path.isfile(input_path):
        output_path = None
        trimage_compress(
            input_path=input_path,
            output_path=output_path,
        )
    elif os.path.isdir(input_path):
        counter = [0]
        def callback_func(input_file, output_file):
            counter[0] += 1
            print(f"正在压缩第{counter[0]}张图片")
            trimage_compress(
                input_path=input_file,
                output_path=output_file,
            )

        input_dir = input_path
        output_dir = f"{input_dir}_无损压缩"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效: {input_path}")