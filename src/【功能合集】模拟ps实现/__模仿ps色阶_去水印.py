import os
import numpy as np
from PIL import Image
import sys
import gc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import batch_process_file_with_callback

from helpers.color_to_gray import color_to_gray

def ps_levels_watermark_removal(input_path, output_path = None, input_black=0, input_white=255, gamma=1.0):
    """
    模拟 PS 色阶调整去除水印
    :param input_path: 原始图片路径
    :param output_path: 输出图片路径
    :param input_black: 黑场阈值 (0-255)，低于此值的像素将变为纯黑
    :param input_white: 白场阈值 (0-255)，高于此值的像素将变为纯白
    :param gamma: 灰度系数/伽马值，控制中间调亮度
    """
    
    try:

        if not output_path:
            base_name, ext = os.path.splitext(input_path)
            output_path = f"{base_name}_output_去水印{ext}"

        img = Image.open(input_path).convert('RGB')
        img_array = np.array(img, dtype=np.float32)
        
        if input_black >= input_white:
            print(f"[错误] {input_path} 处理失败: 黑场阈值必须小于白场阈值！")
            return
            
        clamped = np.clip(img_array, input_black, input_white)
        normalized = (clamped - input_black) / (input_white - input_black)
        corrected = np.power(normalized, 1.0 / gamma)
        result_array = np.clip(corrected * 255, 0, 255).astype(np.uint8)
        
        result_img = Image.fromarray(result_array, 'RGB')
        result_img.save(output_path)
        print(f"[成功] 已保存至: {output_path}")
    except Exception as e:
        print(f"[错误] 处理 {input_path} 时发生异常: {e}")
    finally:
        # ✅【关键】每张处理结束强制释放内存！多张图片时最重要！
        if img is not None:
            img.close()
        del img, img_array, result_array, result_img
        gc.collect()

# --- 使用示例 ---
if __name__ == "__main__":
    # 你可以传入一个图片的路径，也可以传入一个文件夹的路径
    input_path = "/Users/teacher/Downloads/百度网盘Download/去水印/001/历史章节练" 
    input_black = 0
    input_white = color_to_gray("#dcdcdc") + 2

    if os.path.isfile(input_path):
        ps_levels_watermark_removal(
            input_path = input_path,
            input_black=input_black,
            input_white=input_white, 
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            ps_levels_watermark_removal(
                input_path = input_file,
                output_path = output_file,
                input_black=input_black,
                input_white=input_white, 
            )

        output_dir = f'{input_path}_output_去水印'
        batch_process_file_with_callback(
            input_dir=input_path,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效")