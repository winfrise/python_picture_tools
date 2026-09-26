import os, sys
from PIL import Image
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback

def add_bottom_margins(input_path, output_path, fill_color=(255, 255, 255)):
    """
    核心功能：给单张图片增加边距（保持不变）
    """
    try:
        original_img = Image.open(input_path)
        orig_width, orig_height = original_img.size

        new_width = orig_width
        new_height = int(orig_height * (1 + 0.2))

        # 创建新画布并粘贴
        new_img = Image.new(original_img.mode, (new_width, new_height), fill_color)
        new_img.paste(original_img, (0, 0)) # (0, 0) 是位置

        # 保存
        new_img.save(output_path)
        print(f"✅ 成功处理: {os.path.basename(input_path)}")
        return True
    except Exception as e:
        print(f"处理失败 {os.path.basename(input_path)}: {e}")
        return False


# --- 测试调用示例 ---
if __name__ == "__main__":

    input_path="/Users/teacher/Desktop/未命名文件夹/01.png"
    fill_color = (255, 255, 0)

    if os.path.isfile(input_path):
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_bottom{ext}"
        # 单张图片处理
        add_bottom_margins(
            input_path=input_path,
            output_path=output_path,
            fill_color=fill_color
        )
    elif os.path.isdir(input_path):
        def callback_func(input_file, output_file):
            add_bottom_margins(
                input_path=input_file,
                output_path=output_file,
                fill_color=fill_color
            )

        input_dir = input_path
        output_dir = f"{input_path}_output_bottom"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效: {input_path}")