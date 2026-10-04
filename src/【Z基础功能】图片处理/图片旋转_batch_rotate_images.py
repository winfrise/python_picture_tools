from PIL import Image
import os

def batch_rotate_images(input_dir, output_dir, angle):
    """
    批量旋转文件夹中的图片。
    
    参数:
        input_dir (str): 输入图片文件夹路径
        output_dir (str): 输出图片文件夹路径
        angle (float): 旋转角度。按您的要求：正数为顺时针，负数为逆时针
    """
    # 如果输出文件夹不存在，则创建它
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 支持的图片格式
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_formats):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            try:
                with Image.open(input_path) as img:
                    # 转换为 RGB 模式（防止部分 PNG 或 GIF 保存时报错）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 【核心修正】Pillow 默认正值为逆时针，负值为顺时针
                    # 为了满足您“负数为逆时针”的需求，这里对角度取反
                    pil_angle = -angle 
                    
                    # 执行旋转，expand=True 确保旋转后图片完整显示不被裁剪
                    rotated_img = img.rotate(pil_angle, expand=True)
                    
                    # 保存旋转后的图片
                    rotated_img.save(output_path)
                    print(f"成功处理: {filename} (按您的设定旋转 {angle}°)")
                    
            except Exception as e:
                print(f"处理 {filename} 时发生错误: {e}")


# ================= 使用示例 =================
if __name__ == "__main__":
    input_folder = 'xxx'   # 替换为你的输入文件夹路径
    output_folder = 'xxx' # 替换为你的输出文件夹路径
    rotation_angle = -90              # 设置旋转角度，例如 -90 表示逆时针旋转90度<websource>source_group_web_3</websource>

    batch_rotate_images(input_folder, output_folder, rotation_angle)