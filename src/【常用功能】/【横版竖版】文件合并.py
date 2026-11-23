import os
import shutil
from pathlib import Path


def is_hidden(name):
    """判断文件或目录名是否为隐藏（以 . 开头）"""
    return name.startswith('.')


def merge_folders(source_folders, output_folder, operation='copy'):
    """
    将多个文件夹中的文件合并到输出位置，保持各自的相对目录结构，
    跳过隐藏文件和隐藏目录。

    :param source_folders: 源文件夹路径列表
    :param output_folder:  输出文件夹路径
    :param operation:      'copy' 复制（默认） 或 'move' 移动
    :return: dict 统计结果
    """
    if operation not in ('copy', 'move'):
        raise ValueError("operation 参数只能是 'copy' 或 'move'")

    if isinstance(source_folders, (str, os.PathLike)):
        source_folders = [source_folders]

    output_path = Path(output_folder).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    stats = {
        'copied': 0,     # 成功复制/移动文件数
        'skipped': 0,    # 跳过的隐藏文件/无效项
        'conflict': 0,   # 重名冲突（已自动改名）
    }

    for src in source_folders:
        src_path = Path(src).resolve()
        if not src_path.is_dir():
            print(f"[警告] 源文件夹不存在，跳过: {src_path}")
            continue

        print(f"正在处理: {src_path}")

        for root, dirs, files in os.walk(src_path):
            # 原地过滤隐藏目录，os.walk 不再递归进入
            dirs[:] = [d for d in dirs if not is_hidden(d)]

            root_path = Path(root)
            rel_path = root_path.relative_to(src_path)

            for filename in files:
                # 跳过隐藏文件
                if is_hidden(filename):
                    stats['skipped'] += 1
                    continue

                src_file = root_path / filename

                # 目标目录保持相对结构
                target_dir = output_path / rel_path
                target_dir.mkdir(parents=True, exist_ok=True)
                dst_file = target_dir / filename

                # 处理重名冲突
                resolved = _resolve_conflict(dst_file)
                if resolved != dst_file:
                    stats['conflict'] += 1

                if operation == 'copy':
                    shutil.copy2(src_file, resolved)
                else:  # move
                    shutil.move(str(src_file), str(resolved))

                stats['copied'] += 1

    print("=" * 40)
    print(f"合并完成！输出目录: {output_path}")
    print(f"  合并文件数: {stats['copied']}")
    print(f"  重名改名:   {stats['conflict']}")
    print(f"  跳过文件:   {stats['skipped']}")
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
    source_folders = [
        "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/横版图片_统一尺寸_加水印模板_加文字",
        "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/竖版图片_统一尺寸_加水印模板_加文字"
    ]

    output_folder = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/合并"
    operation = "copy" # 可选 copy move
    merge_folders(
        source_folders=source_folders,
        output_folder=output_folder,
        operation=operation   # 改成 'move' 即为移动
    )