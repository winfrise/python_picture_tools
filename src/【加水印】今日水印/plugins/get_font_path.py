def get_font_path(font_name="苹方黑体-中粗-简.ttf"):
    """
    获取项目 assets/fonts 目录下字体的绝对路径。
    
    Args:
        font_name (str): 字体文件名，默认为 "苹方黑体-中粗-简.ttf"
        
    Returns:
        str: 字体的绝对路径字符串。如果文件不存在，返回 None 并打印警告。
    """
    # 1. 获取当前脚本所在的绝对目录
    # __file__ 指向当前代码所在的 .py 文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 向上回退一级到 src 目录，再进入 assets/fonts
    # 假设当前文件在 src/某文件夹/ 下，所以需要 ".."
    font_dir = os.path.join(current_dir, "..", "assets", "fonts")
    
    # 3. 规范化路径（消除 .. 符号）并拼接文件名
    full_path = os.path.normpath(os.path.join(font_dir, font_name))
    
    # 4. 检查文件是否存在
    if os.path.exists(full_path):
        return full_path
    else:
        print(f"⚠️ 警告：未找到字体文件 -> {full_path}")
        return None
