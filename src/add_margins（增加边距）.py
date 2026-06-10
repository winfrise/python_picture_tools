import os
from PIL import Image, UnidentifiedImageError

def add_margins(input_path, margin_params, output_path, fill_color=(255, 255, 255)):
    """
    核心功能：给单张图片增加边距（保持不变）
    """
    try:
        original_img = Image.open(input_path)
        orig_width, orig_height = original_img.size

        # 提取参数
        pad_top = margin_params.get('top', 0)
        pad_bottom = margin_params.get('bottom', 0)
        pad_left = margin_params.get('left', 0)
        pad_right = margin_params.get('right', 0)

        # 计算新尺寸
        new_width = orig_width + pad_left + pad_right
        new_height = orig_height + pad_top + pad_bottom

        # 创建新画布并粘贴
        new_img = Image.new(original_img.mode, (new_width, new_height), fill_color)
        new_img.paste(original_img, (pad_left, pad_top))

        # 保存
        new_img.save(output_path)
        print(f"✅ 成功处理: {os.path.basename(input_path)}")
        return True
    except Exception as e:
        print(f"处理失败 {os.path.basename(input_path)}: {e}")
        return False


def batch_add_margins(input_dir, output_dir, margin_params, fill_color=(255, 255, 255)):
    """
    批量处理：仅负责遍历文件和调用 add_margins
    """
    if not os.path.exists(input_dir):
        print(f"错误：输入文件夹不存在 -> {input_dir}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 支持的后缀
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')

    success_count = 0
    fail_count = 0

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(image_extensions):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            # --- 核心修改点：直接调用 add_margins ---
            if add_margins(input_path, margin_params, output_path, fill_color):
                success_count += 1
            else:
                fail_count += 1

    print(f"处理完成！成功: {success_count}, 失败: {fail_count}")


# --- 测试调用示例 ---
if __name__ == "__main__":

    input_path="/Users/teacher/Desktop/《临床基础检验技术》复习要点/《临床基础检验技术》复习要点_extracted_images"
    output_path="/Users/teacher/Desktop/《临床基础检验技术》复习要点/666"
    color = (0, 0, 0)
    params = {
        "top": 50,
        "bottom": 50,
        "left": 100,
        "right": 100
    }

    # 单张图片处理
    # add_margins(
    #     input_path=input_path,
    #     margin_params=params,
    #     output_path=output_path,
    #     fill_color=color
    # )

    # 批量处理
    batch_add_margins(
        input_dir=input_path,
        output_dir=output_path,
        margin_params=params,
        fill_color=color
    )