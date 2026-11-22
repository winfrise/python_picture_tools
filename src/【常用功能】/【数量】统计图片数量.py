import os
from pathlib import Path
from typing import Optional, Union, List, Dict

# ========== 常量定义 ==========

# 所有格式的通配符
ALL_FORMATS = "*"

# 图片格式常量
IMAGE_FORMATS: List[str] = [".jpg", ".jpeg", ".png"]


# ========== 主函数 ==========

def count_files(
    folder_path: Union[str, Path],
    formats: Union[str, List[str]] = IMAGE_FORMATS,
    recursive: bool = True,
    return_detail: bool = False,
) -> Union[int, Dict[str, int]]:
    """
    统计指定文件夹下的文件数量（包括所有子文件夹中的文件）。
    
    参数:
        folder_path (str | Path): 要统计的文件夹路径
        formats (str | List[str]): 文件格式过滤，支持:
            - "*"                    统计所有格式（默认常量为 ALL_FORMATS）
            - 单个格式，如 ".jpg" 或 "jpg"
            - 多个格式的列表，如 [".jpg", ".png"]
            - 默认值为图片的所有格式（DEFAULT_FORMATS）
        recursive (bool): 是否递归统计子文件夹，默认 True
        return_detail (bool): 是否返回按扩展名分组的详细统计，默认 False
    
    返回:
        int: 文件总数（return_detail=False）
        dict: 包含 total（总数）、visible（显示文件数）、hidden（隐藏文件数）
              以及按扩展名分组的统计（return_detail=True）
    
    示例:
        >>> count_files("./photos")                        # 默认统计所有图片
        123
        >>> count_files("./photos", ALL_FORMATS)           # 统计所有文件
        456
        >>> count_files("./photos", [".jpg", ".png"])      # 统计 jpg 和 png
        78
    """
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"路径不是文件夹: {folder}")

    # ---- 规范化 formats 参数 ----
    match_all = False

    if formats is None:
        match_all = False
    if isinstance(formats, str):
        if formats == ALL_FORMATS:
            match_all = True
        else:
            formats = [formats]
    else:
        if ALL_FORMATS in formats:
            match_all = True

    # 构建统一小写、带点前缀的扩展名集合
    ext_set: Optional[set] = None
    if not match_all:
        if formats is None:
            ext_set = set()
        else:
            ext_set = {
                ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                for ext in formats
            }

    total = 0
    visible_count = 0   # 显示文件数（非隐藏）
    hidden_count = 0    # 隐藏文件数
    detail: Dict[str, int] = {}

    # ---- 遍历策略 ----
    if recursive:
        walker = os.walk(folder)
    else:
        walker = [(str(folder), [], os.listdir(folder))]

    for root, _, files in walker:
        for filename in files:
            ext = Path(filename).suffix.lower()

            # 格式过滤：match_all 为 True 时不过滤
            if not match_all and ext not in ext_set:
                continue

            total += 1

            # 判断是否为隐藏文件
            # Windows: 文件属性为隐藏，或文件名以 "." 开头（跨平台兼容）
            # Unix/Linux/macOS: 文件名以 "." 开头
            is_hidden = filename.startswith(".")
            if not is_hidden:
                # Windows 下再检查文件属性
                full_path = os.path.join(root, filename)
                try:
                    attrs = os.stat(full_path).st_file_attributes
                    # FILE_ATTRIBUTE_HIDDEN = 0x2
                    if attrs & 0x2:
                        is_hidden = True
                except (AttributeError, OSError):
                    # 非 Windows 系统或无权限时忽略
                    pass

            if is_hidden:
                hidden_count += 1
            else:
                visible_count += 1

            if return_detail:
                key = ext if ext else "(无扩展名)"
                detail[key] = detail.get(key, 0) + 1

    if return_detail:
        detail["total"] = total
        detail["visible"] = visible_count
        detail["hidden"] = hidden_count
        return detail

    return total


if __name__ == "__main__":
    folder_path = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/001_横版_竖版_分类"
    formats = ['.jpg', '.png']
    recursive = True       # 是否递归
    return_detail = True   # 是否返回详细

    result = count_files(
        folder_path=folder_path,
        formats=formats,
        recursive=recursive,
        return_detail=return_detail
    )

    print("=" * 40)
    print(f"总文件数   : {result['total']}")
    print(f"显示文件数 : {result['visible']}")
    print(f"隐藏文件数 : {result['hidden']}")
    print("=" * 40)
    print("按扩展名统计:")
    for ext, cnt in result.items():
        if ext not in ("total", "visible", "hidden"):
            print(f"  {ext:15s} : {cnt}")