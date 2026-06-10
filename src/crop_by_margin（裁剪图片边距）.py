import os
from PIL import Image, UnidentifiedImageError


def crop_by_margins(input_path, margin_params, output_path):
    """
    核心功能：根据四周边缘的裁剪厚度来裁剪单张图片（保持不变）
    """
    try:
        original_img = Image.open(input_path)
        width, height = original_img.size

        # 提取参数
        m_left = margin_params.get('left', 0)
        m_top = margin_params.get('top', 0)
        m_right = margin_params.get('right', 0)
        m_bottom = margin_params.get('bottom', 0)

        # 计算保留区域的绝对坐标
        bbox = (
            m_left,
            m_top,
            width - m_right,
            height - m_bottom
        )

        # 执行裁剪并保存
        cropped_img = original_img.crop(bbox)
        cropped_img.save(output_path)
        print(f"✅ 成功裁剪: {os.path.basename(input_path)}")

    except Exception as e:
        print(f"❌ 处理失败 {os.path.basename(input_path)}: {e}")


def batch_crop_by_margins(input_dir, output_dir, margin_params):
    """
    批量调度器：遍历文件夹，调用 crop_by_margins 处理每张图片
    :param input_dir: 输入图片所在的文件夹路径
    :param output_dir: 处理后图片保存的文件夹路径
    :param margin_params: 包含 top, bottom, left, right 的字典
    """
    # 1. 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"错误：输入文件夹不存在 -> {input_dir}")
        return

    # 2. 如果输出目录不存在，则自动创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已自动创建输出文件夹：{output_dir}")

    # 3. 定义支持处理的图片后缀
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')

    # 4. 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_dir):
        # 仅处理图片文件
        if filename.lower().endswith(image_extensions):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            # --- 关键：直接调用核心函数，不重复实现逻辑 ---
            crop_by_margins(
                input_path=input_path,
                margin_params=margin_params,
                output_path=output_path
            )

    print("\n🎉 批量裁剪任务完成！")


# --- 测试调用示例 ---
if __name__ == "__main__":
    input_path="/Users/teacher/Desktop/《临床基础检验技术》复习要点/222/page1_img1.jpeg"
    output_path="/Users/teacher/Desktop/《临床基础检验技术》复习要点/222/page1111333444.jpeg"

    params = {
        "top": 50,      # 从顶部裁剪掉 50px
        "bottom": 50,   # 从底部裁剪掉 50px
        "left": 100,    # 从左侧裁剪掉 100px
        "right": 100    # 从右侧裁剪掉 100px
    }

    # 1. 单个裁剪
    crop_by_margins(
        input_path = input_path,
        margin_params=params,
        output_path = output_path
    )

    # 2. 批量裁剪
    # batch_crop_by_margins(
    #     input_dir=input_path,
    #     output_dir=output_path,
    #     margin_params=params
    # )