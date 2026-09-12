import math

def color_to_gray(color, round_mode='round'):
    """
    将 RGB 或 16进制颜色转换为灰度值
    :param color: 支持 (R,G,B) 元组/列表 或 "#RRGGBB" 字符串
    :param round_mode: 取整模式 ('floor' 向下, 'ceil' 向上, 'round' 四舍五入, 'float' 保留浮点)
    :return: 灰度值
    """
    # 1. 内部处理 16进制颜色字符串
    if isinstance(color, str):
        hex_color = color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError("无效的16进制颜色格式，应为6位字符")
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    elif isinstance(color, (tuple, list)) and len(color) == 3:
        r, g, b = color
    else:
        raise ValueError("颜色格式错误，请传入 (R,G,B) 或 '#RRGGBB'")

    # 2. 计算理论灰度值 (ITU-R BT.601 标准权重)
    gray_float = r * 0.299 + g * 0.587 + b * 0.114

    # 3. 根据模式进行取整
    if round_mode == 'floor':
        return math.floor(gray_float)
    elif round_mode == 'ceil':
        return math.ceil(gray_float)
    elif round_mode == 'round':
        return round(gray_float)
    elif round_mode == 'float':
        return gray_float
    else:
        raise ValueError("不支持的取整模式，可选: floor, ceil, round, float")

