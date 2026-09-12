import os
import glob
import re
from PIL import Image

def natural_sort_key(s):
    """
    用于自然排序的键生成函数。
    它将字符串分割为文本和数字块，并将数字转换为整数进行比较。
    例如: 'img2.jpg' -> ['img', 2, '.jpg']
          'img10.jpg' -> ['img', 10, '.jpg']
    这样 2 < 10，排序就正确了。
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def merge_images_in_folders(input_dir, output_dir = None):


    if output_dir == None:
        parent_dir = os.path.dirname(input_dir)
        output_dir_name = f"{os.path.basename(input_dir)}_图片合并"
        output_dir = os.path.join(parent_dir, output_dir_name)

    # 如果输出目录不存在，则创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[信息] 已创建输出目录: {output_dir}")


    # 获取输入目录下的所有子文件夹
    subfolders = [f.path for f in os.scandir(input_dir) if f.is_dir()]
    
    if not subfolders:
        print("[警告] 输入目录下没有找到任何子文件夹。")
        return

    # 支持的图片后缀（可根据需要扩展）
    img_extensions = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp')

    for folder_path in subfolders:
        folder_name = os.path.basename(folder_path)
        print(f"\n[处理中] 正在处理文件夹: {folder_name}")

        # 1. 收集并排序图片文件
        image_files = []
        for ext in img_extensions:
            image_files.extend(glob.glob(os.path.join(folder_path, ext)))
            image_files.extend(glob.glob(os.path.join(folder_path, ext.upper()))) # 兼容大写后缀
        
        # 核心：按文件名排序
        image_files.sort(key=natural_sort_key)

        if not image_files:
            print(f"  [跳过] 文件夹 '{folder_name}' 中没有找到图片。")
            continue

        # 2. 打开图片并计算拼接后的总尺寸
        images = []
        max_width = 0
        total_height = 0

        try:
            for img_path in image_files:
                img = Image.open(img_path).convert("RGB") # 统一转换为RGB模式，防止RGBA等模式拼接报错
                images.append(img)
                max_width = max(max_width, img.width)
                total_height += img.height
        except Exception as e:
            print(f"  [错误] 读取图片时发生异常: {e}")
            continue

        # 3. 创建画布并纵向拼接
        # 如果图片宽度不一，这里以最大宽度为基准，居中或左对齐（这里采用左对齐，背景填白）
        merged_image = Image.new('RGB', (max_width, total_height), color=(255, 255, 255))
        
        current_y = 0
        for img in images:
            # 如果图片宽度小于最大宽度，可以选择居中或保持原样，这里直接粘贴在左侧
            merged_image.paste(img, (0, current_y))
            current_y += img.height
            img.close() # 及时关闭释放内存

        # 4. 保存结果
        output_path = os.path.join(output_dir, f"{folder_name}.jpg")
        try:
            merged_image.save(output_path, quality=95)
            print(f"  [成功] 已保存: {output_path} (包含 {len(images)} 张图片)")
        except Exception as e:
            print(f"  [错误] 保存图片失败: {e}")
        finally:
            merged_image.close()

# ================= 运行示例 =================
if __name__ == "__main__":
    INPUT_DIRECTORY = "/Users/teacher/Desktop/未命名文件夹 2/2.5氟碳漆铝单板-金奥维_提取的图片"   # 替换为你的输入目录路径
  
    merge_images_in_folders(INPUT_DIRECTORY)