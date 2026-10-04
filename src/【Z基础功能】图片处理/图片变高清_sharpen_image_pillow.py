import os
from PIL import Image, ImageFilter

def sharpen_image(input_path, output_path):
    try: 
        # 打开图片
        img = Image.open(input_path)
        
        # 应用 USM 锐化滤镜
        # radius: 锐化半径，通常为 2 左右
        # percent: 锐化强度，150% 表示增强程度
        # threshold: 阈值，控制多大程度的颜色差异才会被锐化，避免放大噪点
        sharpened_img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        # 保存处理后的图片
        sharpened_img.save(output_path)
        print(f"图片已锐化并保存至: {output_path}")
        return True
    
    except Exception as e:
        print(f"❌ 处理失败 {os.path.basename(input_path)}: {e}")
        return False

def batch_sharpen_image(input_dir, output_dir):
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
            sharpen_image(
                input_path=input_path,
                output_path=output_path
            )

    print("\n🎉 批量任务完成！")

# --- 测试调用示例 ---
if __name__ == "__main__":

    input_path="/Users/teacher/Desktop/《临床基础检验技术》复习要点/《临床基础检验技术》复习要点_extracted_images"
    output_path="/Users/teacher/Desktop/《临床基础检验技术》复习要点/《临床基础检验技术》复习要点_extracted_images333"

    if os.path.isfile(input_path):
        batch_sharpen_image(
            input_dir=input_path,
            output_dir=output_path
        )
    else:
        sharpen_image(
            input_path=input_path,
            output_path=output_path
        )

