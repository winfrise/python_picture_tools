import os
import math
from PIL import Image
from utils import batch_process_file_with_callback

def split_image(input_path, direction="vertical", mode="count", value=2, output_dir=None):
    """
    图片分割工具
    
    参数说明:
    - input_path: 原图路径
    - direction: 分割方向 ("vertical" 垂直分割, "horizontal" 水平分割)
    - mode: 分割模式 ("count" 按数量, "size" 按宽度/高度像素值)
    - value: 具体数值 (如果是count模式就是切几块，如果是size模式就是每块的像素宽/高)
    - output_dir: 输出文件夹
    """
    try:
        img = Image.open(input_path)
        width, height = img.size
    except Exception as e:
        print(f"打开图片失败: {e}")
        return

    if not output_dir:
        base_name, ext = os.path.splitext(input_path)
        output_dir = f"{base_name}_output_split"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_name, file_ext = os.path.splitext(os.path.basename(input_path))
    
    # 确定分割的总长度和每块的大小
    if direction == "vertical":
        total_length = width
        split_size = value if mode == "size" else (width // value)
    else: # horizontal
        total_length = height
        split_size = value if mode == "size" else (height // value)

    # 计算需要切分的块数
    if mode == "size":
        # 按尺寸分割时，向上取整计算块数
        split_count = math.ceil(total_length / split_size)
    else:
        split_count = value

    print(f"开始分割: 方向={direction}, 模式={mode}, 预计生成 {split_count} 张图片...")

    for i in range(split_count):
        if direction == "vertical":
            left = i * split_size
            # 最后一块直接切到图片边缘，防止像素丢失
            right = width if i == split_count - 1 else (i + 1) * split_size
            # 裁剪区域 (左, 上, 右, 下)
            box = (left, 0, right, height)
        else:
            top = i * split_size
            # 最后一块直接切到图片边缘
            bottom = height if i == split_count - 1 else (i + 1) * split_size
            # 裁剪区域 (左, 上, 右, 下)
            box = (0, top, width, bottom)

        # 裁剪并保存
        cropped_img = img.crop(box)
        output_path = os.path.join(output_dir, f"{file_name}_{direction}_{i+1}{file_ext}")
        cropped_img.save(output_path)
        print(f"已保存: {output_path}")

def batch_split_image(input_dir):
    def callback_func(input_file, output_file):
        split_image(
            input_path = input_file,
            direction=DIRECTION, 
            mode=MODE, 
            value=VALUE,
        )
    batch_process_file_with_callback(
        input_dir = input_dir,
        output_dir= "NOT_SAVE",
        callback_func=callback_func
    )


# ================= 使用示例 =================
if __name__ == "__main__":

    IMAGE_PATH = "/Volumes/西数4T外置/拼多多图片/图文速改（通用详情页）/海龟详情页.png" # 替换成你的图片路径
    DIRECTION = "horizontal" #  ("vertical" 垂直分割, "horizontal" 水平分割)
    MODE = "count" # 分割模式 ("count" 按数量, "size" 按宽度/高度像素值)
    VALUE = 12 # 具体数值 (如果是count模式就是切几块，如果是size模式就是每块的像素宽/高)


    if os.path.isfile(IMAGE_PATH):
        # 单张图片处理
        split_image(
            input_path=IMAGE_PATH,
            direction=DIRECTION, 
            mode=MODE, 
            value=VALUE,
        )

    elif os.path.isdir(IMAGE_PATH):
        # 批量处理
        input_dir = IMAGE_PATH
        batch_split_image(
            input_dir=input_dir,
        )