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
    gamma=1.0           # 灰场(Gamma)：0.1-10.0，默认1.0 (1.0为不调整)
):
    """
    调整图像的色阶（黑场、白场、灰场）
    """

    print(f"正在处理完件{input_path}")
    # 1. 打开并转为 RGB 模式以保留色彩
    img = Image.open(input_path).convert("RGB")

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
            # 使用 pow 函数进行非线性调整
            # 注意：gamma 值越小图越亮，通常 UI 上显示的 "1.00" 对应计算中的指数 1/1.0
            corrected = pow(normalized, 1.0 / gamma)
            val = corrected * 255.0
        
        # 确保数值在 0-255 之间并取整
        lut.append(int(min(max(val, 0), 255)))

    # 3. 应用 LUT 到 RGB 三个通道
    # PIL 的 point 方法对于多通道图像需要长度为 256 * channels 的列表
    # 这里我们将同一个 LUT 复制 3 份分别给 R, G, B
    lut_rgb = lut * 3
    
    new_img = img.point(lut_rgb)
    new_img.save(output_path)
    
    print(f"处理完成！黑场:{black_point}, 白场:{white_point}, Gamma:{gamma}")



if __name__ == "__main__":
    # 你可以传入一个图片的路径，也可以传入一个文件夹的路径
    input_path = "/Users/teacher/Downloads/未命名文件夹/图片"
    white_point = 220 # 默认值:  255
    black_point = 35 # 默认值: 0
    gamma = 1.0 # 默认值: 1.0

    if os.path.isfile(input_path):
        base_name, ext = os.path.split
        output_path = f"{base_name}_调色阶{ext}"
        adjust_levels(
            input_path = input_path, 
            output_path = output_path, 
            white_point = white_point,
            black_point=black_point,
            gamma=gamma
        )

    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            adjust_levels(
                input_path = input_file, 
                output_path = output_file, 
                white_point = white_point,
                black_point=black_point,
                gamma=gamma
            )

        output_dir = f'{input_path}_调色阶'
        batch_process_file_with_callback(
            input_dir=input_path,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效")