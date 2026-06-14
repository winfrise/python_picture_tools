import os
from PIL import Image, ImageEnhance

def adjust_brightness_contrast(input_path, output_path, brightness=1.0, contrast=1.0):
    """
    调整图片的亮度和对比度
    
    Args:
        input_path (str): 输入图片的文件路径
        output_path (str): 输出图片的文件路径
        brightness (float): 亮度因子，1.0为原始亮度，>1变亮，<1变暗
        contrast (float): 对比度因子，1.0为原始对比度，>1增强，<1减弱
        
    Returns:
        bool: 处理成功返回 True，失败返回 False
    """
    try:
        # 打开原始图像
        img = Image.open(input_path)
        
        # 调整亮度
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
            
        # 调整对比度
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
            
        # 保存处理后的图像
        img.save(output_path)
        print(f"处理成功！已保存至: {output_path}")
        return True
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{input_path}'")
        return False
    except Exception as e:
        print(f"处理图像时出错: {e}")
        return False

def batch_adjust_brightness_contrast(input_dir, output_dir, brightness, contrast):
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
            adjust_brightness_contrast(
                input_path=input_path,
                output_path=output_path,
                brightness=brightness,
                contrast=contrast
            )

    print("\n🎉 批量任务完成！")

# --- 使用示例 ---
adjust_brightness_contrast(
    '/Users/teacher/Desktop/《临床基础检验技术》复习要点/test/page4_img1.jpeg', 
    '/Users/teacher/Desktop/《临床基础检验技术》复习要点/test/page4_img13333.jpeg', brightness=1.3, contrast=1.5)


# --- 测试调用示例 ---
if __name__ == "__main__":

    input_path="/Users/teacher/Desktop/《临床基础检验技术》复习要点/《临床基础检验技术》复习要点_extracted_images"
    output_path="/Users/teacher/Desktop/《临床基础检验技术》复习要点/333555"
    # 亮度因子，1.0为原始亮度，>1变亮，<1变暗
    brightness=1.3
    # 对比度因子，1.0为原始对比度，>1增强，<1减弱
    contrast=1.5

    if os.path.isfile(input_path):
        batch_adjust_brightness_contrast(
            input_dir=input_path,
            output_dir=output_path,
            brightness=brightness,
            contrast=contrast
        )
    else:
        adjust_brightness_contrast(
            input_path=input_path,
            output_path=output_path,
            brightness=brightness,
            contrast=contrast
        )
