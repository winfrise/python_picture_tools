import os
import shutil
from pathlib import Path
from PIL import Image

# 支持的图片扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}


def is_hidden(name):
    """判断文件或目录名是否为隐藏（以 . 开头）"""
    return name.startswith('.')


def classify_images_by_size(input_folder, output_folder, operation='copy'):
    """
    将输入文件夹中的图片按“完全相同的尺寸（宽x高）”分类到输出文件夹。
    同尺寸图片放入同一个文件夹，文件夹名为 宽x高，例如 1920x1080。

    :param input_folder: 输入文件夹路径
    :param output_folder: 输出文件夹路径
    :param operation: 'copy' 复制（默认） 或 'move' 移动
    :return: dict 统计结果
    """
    if operation not in ('copy', 'move'):
        raise ValueError("operation 参数只能是 'copy' 或 'move'")

    input_path = Path(input_folder).resolve()
    output_path = Path(output_folder).resolve()

    if not input_path.is_dir():
        raise NotADirectoryError(f"输入文件夹不存在: {input_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    stats = {}      # 尺寸 -> 数量
    skipped = 0

    for root, dirs, files in os.walk(input_path):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not is_hidden(d)]

        root_path = Path(root)
        rel_path = root_path.relative_to(input_path)

        for filename in files:
            if is_hidden(filename):
                skipped += 1
                continue

            src_file = root_path / filename
            ext = src_file.suffix.lower()

            if ext not in IMAGE_EXTENSIONS:
                skipped += 1
                continue

            # 读取图片尺寸
            try:
                with Image.open(src_file) as img:
                    width, height = img.size
            except Exception as e:
                print(f"[警告] 无法读取图片 {src_file}: {e}")
                skipped += 1
                continue

            # 按完全相同尺寸分组，文件夹名如 1920x1080
            size_key = f"{width}x{height}"
            stats[size_key] = stats.get(size_key, 0) + 1

            # 保持原有层级结构
            target_dir = output_path / size_key / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            dst_file = target_dir / filename
            dst_file = _resolve_conflict(dst_file)

            if operation == 'copy':
                shutil.copy2(src_file, dst_file)
            else:  # move
                shutil.move(str(src_file), str(dst_file))

    # 打印统计（按图片数量从多到少排序）
    print("=" * 40)
    print(f"处理完成！输出目录: {output_path}")
    total = 0
    for size_key in sorted(stats.keys(), key=lambda k: stats[k], reverse=True):
        w, h = size_key.split('x')
        print(f"  {size_key} ({w}宽 x {h}高): {stats[size_key]} 张")
        total += stats[size_key]
    print(f"  跳过文件: {skipped} 个")
    print(f"  处理图片合计: {total} 张")
    print(f"  不同尺寸种类: {len(stats)} 种")
    print("=" * 40)

    return stats


def _resolve_conflict(dst_file: Path) -> Path:
    """
    如果目标文件已存在，自动追加序号，避免覆盖。
    """
    if not dst_file.exists():
        return dst_file

    stem = dst_file.stem
    suffix = dst_file.suffix
    parent = dst_file.parent
    i = 1
    while True:
        new_file = parent / f"{stem}_{i}{suffix}"
        if not new_file.exists():
            return new_file
        i += 1


if __name__ == '__main__':
    input_folder = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/竖版图片_统一尺寸"
    output_folder = f"{input_folder}_按尺寸分类"
    operation = "copy"  # 可选 'copy' 或 'move'

    classify_images_by_size(
        input_folder=input_folder,
        output_folder=output_folder,
        operation=operation,
    )