from PIL import Image
import os

def split_a4(image_path, output_dir="output"):
    """
    将竖长图按 A4 比例裁剪
    A4 比例: 210 x 297 mm -> 宽高比约 0.707
    """
    # A4 标准比例 (宽 / 高)
    A4_RATIO = 210 / 297 
    
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    # 1. 计算裁剪后的宽度（保持原图宽度，按 A4 比例算高度，或者固定宽度）
    # 这里采用：保持原图宽度不变，计算对应的 A4 高度
    crop_height = int(img_width / A4_RATIO)
    
    if crop_height >= img_height:
        print("图片高度不足一张 A4，无需裁剪。")
        return

    os.makedirs(output_dir, exist_ok=True)
    
    count = 1
    y = 0
    while y < img_height:
        # 处理最后一张：如果剩余高度不够，则补白边
        if y + crop_height > img_height:
            # 创建一张标准 A4 比例的空白图
            new_img = Image.new("RGB", (img_width, crop_height), (255, 255, 255))
            # 把剩余部分贴上去
            new_img.paste(img.crop((0, y, img_width, img_height)), (0, 0))
        else:
            new_img = img.crop((0, y, img_width, y + crop_height))
        
        save_path = os.path.join(output_dir, f"page_{count:02d}.png")
        new_img.save(save_path)
        print(f"已保存: {save_path}")
        
        y += crop_height
        count += 1

# 使用示例
if __name__ == "__main__":
    # 替换为你的图片路径
    image_path = "/Users/teacher/Desktop/未命名文件夹/安装式模拟电流电压表使用说明书-浙江正泰仪器仪表_260709_提取的图片/page1_img1.jpeg"
    output_dir = "/Users/teacher/Desktop/未命名文件夹/output"
    split_a4(
        image_path = image_path,
        output_dir = output_dir 
    )