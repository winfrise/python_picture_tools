import os
import subprocess
from PIL import Image

# 查看.icns文件中的图片命令
# iconutil -c iconset "/Users/teacher/Desktop/未命名文件夹 2/icons_output/AppIcon_backup.icns"

def create_icns(png_path, icns_name="MyAppIcon"):
    # 1. 获取源图片所在的绝对目录路径
    source_dir = os.path.dirname(os.path.abspath(png_path))
    
    # 2. 在源图片目录下创建 icons_output 文件夹
    output_dir = os.path.join(source_dir, "icons_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 3. 定义 .iconset 文件夹路径（放在 icons_output 内部）
    iconset_dir = os.path.join(output_dir, f"{icns_name}.iconset")
    os.makedirs(iconset_dir, exist_ok=True)

    # 4. 打开源图片
    try:
        img = Image.open(png_path)
        # 确保图片带有透明通道，如果是 JPG 则自动转换为 RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
    except FileNotFoundError:
        print(f"错误：找不到图片 {png_path}，请确保路径正确。")
        return
    except Exception as e:
        print(f"打开图片失败：{e}")
        return

    # 5. 定义需要生成的尺寸列表 (尺寸, @1x文件名, @2x文件名)
    sizes = [
        (16, "icon_16x16.png", "icon_16x16@2x.png"),
        (32, "icon_32x32.png", "icon_32x32@2x.png"),
        (64, "icon_64x64.png", None),
        (128, "icon_128x128.png", "icon_128x128@2x.png"),
        (256, "icon_256x256.png", "icon_256x256@2x.png"),
        (512, "icon_512x512.png", "icon_512x512@2x.png"),
    ]

    # 6. 循环生成不同尺寸的 PNG
    for size, name_1x, name_2x in sizes:
        resized_img = img.resize((size, size), Image.LANCZOS)
        resized_img.save(os.path.join(iconset_dir, name_1x))
        if name_2x:
            resized_img_2x = img.resize((size * 2, size * 2), Image.LANCZOS)
            resized_img_2x.save(os.path.join(iconset_dir, name_2x))

    print(f"成功生成所有尺寸的 PNG 到 {iconset_dir}")

    # 7. 调用 macOS 原生命令 iconutil 打包为 .icns
    output_icns = os.path.join(output_dir, f"{icns_name}.icns")
    cmd = ["iconutil", "-c", "icns", iconset_dir, "-o", output_icns]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"成功生成 .icns 文件：{output_icns}")
    except subprocess.CalledProcessError:
        print("打包失败，请确保当前系统是 macOS 且已安装 iconutil。")
    except FileNotFoundError:
        print("错误：找不到 iconutil 命令，此脚本仅支持在 macOS 上运行。")

if __name__ == "__main__":
    png_path = "/Users/teacher/Desktop/未命名文件夹 2/微信_图标.png"
    icns_name = "WeChatIcon"
    # 示例：传入你的图片路径（支持相对路径或绝对路径）
    create_icns(png_path, icns_name)