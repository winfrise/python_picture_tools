import os
import shutil
from pathlib import Path
from PIL import Image

# 支持的图片扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}


def is_hidden(name):
    """判断文件或目录名是否为隐藏（以 . 开头）"""
    return name.startswith('.')


def classify_images(input_folder, output_folder, operation='copy'):
    """
    将输入文件夹中的图片按横版/竖版分类到输出文件夹。

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

    # 创建横版、竖版目标文件夹
    landscape_dir = output_path / '横版图片'
    portrait_dir = output_path / '竖版图片'
    landscape_dir.mkdir(parents=True, exist_ok=True)
    portrait_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        'landscape': 0,   # 横版
        'portrait': 0,    # 竖版
        'square': 0,      # 正方形（宽==高，归入横版，可自行调整）
        'skipped': 0,     # 非图片、隐藏文件或读取失败
    }

    for root, dirs, files in os.walk(input_path):
        # 原地修改 dirs，跳过隐藏目录（os.walk 就不会再进入这些目录）
        dirs[:] = [d for d in dirs if not is_hidden(d)]

        root_path = Path(root)
        # 计算相对于输入根目录的相对路径，用于保持层级
        rel_path = root_path.relative_to(input_path)

        for filename in files:
            # 跳过隐藏文件
            if is_hidden(filename):
                stats['skipped'] += 1
                continue

            src_file = root_path / filename
            ext = src_file.suffix.lower()

            if ext not in IMAGE_EXTENSIONS:
                stats['skipped'] += 1
                continue

            # 判断横竖版
            try:
                with Image.open(src_file) as img:
                    width, height = img.size
            except Exception as e:
                print(f"[警告] 无法读取图片 {src_file}: {e}")
                stats['skipped'] += 1
                continue

            if width > height:
                category = 'landscape'
                target_root = landscape_dir
            elif height > width:
                category = 'portrait'
                target_root = portrait_dir
            else:
                # 正方形默认归入横版，可改成 portrait 或单独处理
                category = 'square'
                target_root = landscape_dir

            # 保持原有层级结构
            target_dir = target_root / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            dst_file = target_dir / filename

            # 处理重名文件（避免覆盖）
            dst_file = _resolve_conflict(dst_file)

            # 执行复制或移动
            if operation == 'copy':
                shutil.copy2(src_file, dst_file)
            else:  # move
                shutil.move(str(src_file), str(dst_file))

            stats[category] += 1

    print("=" * 40)
    print(f"处理完成！输出目录: {output_path}")
    print(f"  横版图片: {stats['landscape'] + stats['square']} 张 "
          f"(其中正方形 {stats['square']} 张)")
    print(f"  竖版图片: {stats['portrait']} 张")
    print(f"  跳过文件: {stats['skipped']} 个")
    print(f"  显示文件合计: {stats['landscape'] + stats['square'] + stats['portrait']}  张")
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
    input_folder = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/001"
    output_folder = f"{input_folder}_横版_竖版_分类"
    operation = "copy" # 可选copy , move

    classify_images(
        input_folder=input_folder,
        output_folder=output_folder,
        operation=operation   # 改成 'move' 即为移动
    )