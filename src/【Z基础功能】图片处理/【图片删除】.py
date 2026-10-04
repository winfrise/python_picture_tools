import os
from PIL import Image
from dataclasses import dataclass
from typing import Callable, Optional

# 定义一个数据类，用于统一封装图片的各项信息
@dataclass
class ImageInfo:
    file_path: str      # 文件绝对路径
    file_name: str      # 文件名
    file_size: int      # 文件体积大小（字节）
    width: int          # 图片宽度
    height: int         # 图片高度

# 定义类型别名，让代码可读性更好
DeleteCondition = Callable[[ImageInfo], bool]


# ================= 外部常用的条件判断函数 =================

def by_file_size(max_size_kb: float) -> DeleteCondition:
    """按文件体积判断：删除小于指定大小(KB)的图片"""
    def condition(info: ImageInfo) -> bool:
        return info.file_size < max_size_kb * 1024
    return condition

def by_resolution(min_width: int, min_height: int) -> DeleteCondition:
    """按像素尺寸判断：删除宽度或高度小于指定值的图片"""
    def condition(info: ImageInfo) -> bool:
        return info.width < min_width or info.height < min_height
    return condition

def by_file_name(keyword: str) -> DeleteCondition:
    """按文件名判断：删除文件名包含指定关键字的图片"""
    def condition(info: ImageInfo) -> bool:
        return keyword in info.file_name
    return condition


# ================= 核心遍历与删除逻辑 =================

def clean_images(directory: str, condition: DeleteCondition, dry_run: bool = True):
    """
    遍历文件夹并删除满足条件的图片
    :param directory: 目标文件夹路径
    :param condition: 接收 ImageInfo 并返回 bool 的判断函数
    :param dry_run: 默认为 True（安全模式，仅打印不删除），设为 False 时执行真实删除
    """
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.lower().endswith(image_extensions):
                continue

            file_path = os.path.join(root, file)
            try:
                # 获取文件体积
                file_size = os.path.getsize(file_path)
                
                # 获取图片尺寸
                with Image.open(file_path) as img:
                    width, height = img.size

                # 封装图片信息
                info = ImageInfo(
                    file_path=file_path,
                    file_name=file,
                    file_size=file_size,
                    width=width,
                    height=height
                )

                # 执行传入的判断函数
                if condition(info):
                    if dry_run:
                        print(f"[预览] 待删除: {file_path} | 大小: {file_size}B | 尺寸: {width}x{height}")
                    else:
                        os.remove(file_path)
                        print(f"[已删除] {file_path}")

            except Exception as e:
                print(f"[跳过] 无法处理: {file_path}, 错误: {e}")


# ================= 使用示例 =================

if __name__ == "__main__":
    target_folder = "/Users/teacher/Downloads/百度网盘Download/未命名文件夹/未命名文件夹/2026孔老师笔记（下册）(1)__提取的图片"  # 替换为你的实际图片目录路径

    def custom_condition(img_info):
        width = img_info.width
        height = img_info.height
        if (width == 260 & height == 260):
            return True
        return False
    
    clean_images(target_folder, condition=custom_condition, dry_run=False)
    # 1. 删除小于 10KB 的图片
    # clean_images(target_folder, condition=by_file_size(10), dry_run=False)

    # 2. 删除宽高小于 100px 的图片
    # clean_images(target_folder, condition=by_resolution(100, 100), dry_run=False)

    # 3. 删除文件名包含 "temp" 的图片
    # clean_images(target_folder, condition=by_file_name("temp"), dry_run=False)

    # 4. 组合条件：删除小于 10KB 且 宽高小于 100px 的图片
    # combined_condition = lambda info: by_file_size(10)(info) and by_resolution(100, 100)(info)
    # clean_images(target_folder, condition=combined_condition, dry_run=False)