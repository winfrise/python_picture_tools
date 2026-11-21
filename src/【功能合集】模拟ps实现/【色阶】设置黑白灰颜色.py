from PIL import Image
import os, sys

# 假设你的项目结构需要这一行来导入 utils，保持原样
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback


def adjust_levels(
    input_path,
    output_path,
    black_point=0,      # 黑场：0-254，默认0
    white_point=255,    # 白场：1-255，默认255
    gamma=1.0,          # 灰场(Gamma)：0.1-10.0，默认1.0 (1.0为不调整)
    to_grayscale=False  # 新增：是否先转灰度再调色阶
):
    """
    调整图像的色阶（黑场、白场、灰场）
    to_grayscale=True 时，先转为灰度图再应用色阶，输出为灰度图。
    """

    print(f"正在处理{input_path}")

    # 1. 打开图片；根据参数决定是否先转灰度
    img = Image.open(input_path)
    if to_grayscale:
        img = img.convert("L")   # 单通道灰度
        channels = 1
    else:
        img = img.convert("RGB") # 三通道彩色
        channels = 3

    # 参数安全检查，防止除以零或逻辑错误
    if black_point >= white_point:
        print("错误：黑场阈值必须小于白场阈值")
        return
    if gamma <= 0:
        print("错误：Gamma 值必须大于 0")
        return

    # 2. 构建查找表 (LUT)
    lut = []
    range_diff = white_point - black_point

    for i in range(256):
        # 第一步：处理黑场和白场（线性拉伸）
        if i <= black_point:
            val = 0.0
        elif i >= white_point:
            val = 255.0
        else:
            # 将 [black, white] 映射到 [0, 1] 之间
            normalized = (i - black_point) / float(range_diff)

            # 第二步：处理灰场（Gamma 校正）
            # gamma 值越小图越亮，UI 上 "1.00" 对应计算中的指数 1/1.0
            corrected = pow(normalized, 1.0 / gamma)
            val = corrected * 255.0

        # 确保数值在 0-255 之间并取整
        lut.append(int(min(max(val, 0), 255)))

    # 3. 应用 LUT
    # 灰度图只需 256 长度；RGB 图需要 256 * 3
    lut_applied = lut * channels
    new_img = img.point(lut_applied)
    new_img.save(output_path)

    print(f"处理完成！灰度:{to_grayscale}, 黑场:{black_point}, 白场:{white_point}, Gamma:{gamma}")


if __name__ == "__main__":
    # 你可以传入一个图片的路径，也可以传入一个文件夹的路径
    input_path = "/Volumes/西数4T外置/百度网盘默认下载/第二+三阶段 数学卷/第二+三阶段 数学卷__合成的图片_DPI_300_调色阶"
    white_point = 255   # 默认值: 255
    black_point = 165     # 默认值: 0
    gamma = 1.0         # 默认值: 1.0
    to_grayscale = True # 新增：True 先转灰度，False 保留彩色

    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)   # 修正原代码的笔误
        output_path = f"{base_name}_调色阶{ext}"
        adjust_levels(
            input_path=input_path,
            output_path=output_path,
            white_point=white_point,
            black_point=black_point,
            gamma=gamma,
            to_grayscale=to_grayscale
        )

    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            dir_name = os.path.dirname(output_file)
            os.makedirs(dir_name, exist_ok=True)
            adjust_levels(
                input_path=input_file,
                output_path=output_file,
                white_point=white_point,
                black_point=black_point,
                gamma=gamma,
                to_grayscale=to_grayscale
            )

        output_dir = f'{input_path}_调色阶'
        batch_process_file_with_callback(
            input_dir=input_path,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效")