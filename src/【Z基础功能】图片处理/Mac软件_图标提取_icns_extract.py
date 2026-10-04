import os
import subprocess

def extract_icns(icns_path, output_dir=None):
    """
    将 .icns 文件解包为 .iconset 文件夹（包含所有尺寸的 PNG 图片）
    
    :param icns_path: .icns 文件的绝对或相对路径
    :param output_dir: 解包后的 .iconset 文件夹存放路径（可选）
                       如果不传，默认保存在源 .icns 文件的同级目录下
    :return: 成功返回 True，失败返回 False
    """
    # 1. 检查源文件是否存在
    if not os.path.exists(icns_path):
        print(f"❌ 错误：找不到文件 {icns_path}")
        return False

    # 2. 确定输出目录和最终的 iconset 路径
    # 获取源文件的绝对路径和所在目录
    abs_icns_path = os.path.abspath(icns_path)
    source_dir = os.path.dirname(abs_icns_path)
    base_name = os.path.splitext(os.path.basename(abs_icns_path))[0]

    if output_dir is None:
        # 【默认行为】：输出到源文件的同级目录，并自动命名为 "文件名.iconset"
        final_iconset_path = os.path.join(source_dir, f"{base_name}.iconset")
    else:
        # 【自定义行为】：输出到用户指定的目录
        os.makedirs(output_dir, exist_ok=True)
        final_iconset_path = os.path.join(output_dir, f"{base_name}.iconset")

    # 3. 构建 iconutil 命令
    # iconutil -c iconset <输入文件> -o <输出目标路径>
    cmd = ["iconutil", "-c", "iconset", abs_icns_path, "-o", final_iconset_path]

    try:
        # 4. 执行系统命令
        subprocess.run(cmd, check=True)
        print(f"✅ 解包成功！")
        print(f"📂 生成的 .iconset 文件夹位于：{final_iconset_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 解包失败：iconutil 命令执行出错。请确保文件是有效的 .icns 格式。")
        return False
    except FileNotFoundError:
        print("❌ 系统错误：找不到 iconutil 命令。此功能仅支持在 macOS 上运行。")
        return False


if __name__ == "__main__":
    icns_path = "/Users/teacher/Desktop/未命名文件夹 2/icons_output/AppIcon_backup.icns"
    extract_icns(icns_path)