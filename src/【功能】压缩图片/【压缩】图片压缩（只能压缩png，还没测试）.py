import os
import subprocess
from pathlib import Path

def batch_compress_png(input_dir, output_dir, quality="65-80", speed=4):
    """
    批量调用 pngquant 压缩 PNG 图片
    :param input_dir: 输入目录
    :param output_dir: 输出目录
    :param quality: 质量范围 (例如 '65-80')
    :param speed: 压缩速度 (1-11，1质量最好但最慢，4为默认平衡，11最快)
    """
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    for png_file in input_path.glob("**/*.png"):
        # 保持原有的相对目录结构
        relative_path = png_file.relative_to(input_path)
        target_file = output_path / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "pngquant",
            "--quality", quality,
            "--speed", str(speed),
            "--force",
            "--skip-if-larger",  # 如果压缩后反而变大，则跳过
            "--output", str(target_file),
            str(png_file)
        ]

        try:
            # 执行压缩
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ 成功: {relative_path}")
        except subprocess.CalledProcessError as e:
            # pngquant 在质量低于设定最小值时会返回错误码 99
            if e.returncode == 99:
                print(f"⚠️ 跳过(质量过低): {relative_path}")
            else:
                print(f"❌ 失败: {relative_path}, 错误: {e.stderr.decode()}")

# 使用示例
if __name__ == "__main__":
    batch_compress_png("/Users/teacher/Desktop/百度网盘下载/未命名文件夹/方兴未“艾”——千年艾草活化开发与利用的领航者__合成的图片_DPI_300", "/Users/teacher/Desktop/百度网盘下载/未命名文件夹/方兴未“艾”——千年艾草活化开发与利用的领航者__合成的图片_DPI_3002", quality="70-85", speed=3)