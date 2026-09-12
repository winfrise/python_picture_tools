import numpy as np
import cv2
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.rgb_to_gray import rgb_to_gray

def adjust_levels(
        input_path, 
        black_color, 
        white_color, 
        gamma=1.0, 
        out_shadows=0, 
        out_highlights=255, 
        output_path=None
    ):
    """
    模拟Photoshop色阶调整，支持自动命名并保存图片
    """
    # 1. 读取图片
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到图片文件: {input_path}")
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"无法读取图片，请检查文件是否损坏: {input_path}")


    in_shadows=black_color
    in_highlights=white_color

    # 2. 色阶核心算法
    img_float = image.astype(np.float32)
    img_clipped = np.clip(img_float, in_shadows, in_highlights)
    img_normalized = (img_clipped - in_shadows) / (in_highlights - in_shadows + 1e-8)
    img_gamma = np.power(img_normalized, 1.0 / gamma)
    img_output = img_gamma * (out_highlights - out_shadows) + out_shadows
    result = np.clip(img_output, 0, 255).astype(np.uint8)

    # 3. 处理保存路径
    if output_path is None:
        # 获取原图所在目录、文件名、后缀
        dir_name = os.path.dirname(input_path) or '.'  # 防止空字符串
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        extension = os.path.splitext(input_path)[1]
        
        # 拼接新文件名：原文件名_output_黑场白场.后缀
        new_filename = f"{base_name}_output_{in_shadows}{out_highlights}{extension}"
        output_path = os.path.join(dir_name, new_filename)

    # 4. 保存图片
    cv2.imwrite(output_path, result)
    print(f"✅ 处理完成！已保存至: {output_path}")
    return result

# --- 使用示例 ---
if __name__ == "__main__":
    # 传入图片路径，调整黑场为20，白场为230，提亮中间调(gamma=0.8)
    input_path = "/Users/teacher/Desktop/青岛大学附属医院总务设备采购项目002(二次)-1（产品原材料）/青岛大学_页面_243.jpg"
    black_color = 30
    white_color = 255
    adjust_levels(
        input_path=input_path, 
        black_color=black_color, 
        white_color=white_color, 
        gamma=0.8
    )
    