import re

def natural_sort(items, key=None):
    """
    对列表进行自然排序（模拟电脑文件管理器的排序方式）。
    
    :param items: 待排序的列表
    :param key: 提取排序字段的函数。如果是对象列表，传入如 lambda x: x['filename']；如果是普通字符串列表，传 None 即可。
    :return: 排序后的新列表（不修改原列表）
    """
    # 核心：将字符串拆分为 [文本, 数字, 文本, 数字...] 的列表
    # 例如: "image10.jpg" -> ['image', 10, '.jpg']
    # 比较时，Python 会按顺序比较列表元素：字符串按字典序，数字按大小
    def convert(text):
        return int(text) if text.isdigit() else text.lower()

    def natural_key(item):
        # 1. 先通过传入的 key 函数获取实际的字符串（如果 key 为 None，则 item 本身就是字符串）
        target_str = str(key(item)) if key else str(item)
        # 2. 使用正则表达式按数字边界切分，并将数字部分转为整数
        return [convert(c) for c in re.split(r'(\d+)', target_str)]

    return sorted(items, key=natural_key)