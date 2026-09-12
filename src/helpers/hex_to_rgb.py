def hex_to_rgb(hex_color: str) -> list:
    """
    将 16 进制颜色字符串转换为 RGB 列表 [R, G, B]
    
    Args:
        hex_color: 16进制颜色字符串 (例如 "#FF5733" 或 "FF5733")
        
    Returns:
        包含 R, G, B 三个整数的列表
    """
    # 1. 去除可能存在的 '#' 号并转为大写
    hex_color = hex_color.lstrip('#').upper()
    
    # 2. 简单的格式校验
    if len(hex_color) != 6:
        raise ValueError(f"无效的 16 进制颜色格式: {hex_color}，长度应为 6 位")
        
    try:
        # 3. 切片提取 R, G, B 并转为 10 进制整数
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        return [r, g, b]
    except ValueError:
        raise ValueError(f"包含非 16 进制字符: {hex_color}")

# --- 使用示例 ---
color_hex = "#3A8F2B"
rgb_list = hex_to_rgb(color_hex)
print(f"Hex: {color_hex} -> RGB: {rgb_list}") 
# 输出: Hex: #3A8F2B -> RGB: [58, 143, 43]