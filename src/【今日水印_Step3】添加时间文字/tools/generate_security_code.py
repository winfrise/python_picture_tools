import random
import string
def generate_security_code(length=14, max_digits=4, exclude_chars="Q"):
    """
    生成指定长度的随机字符串，支持排除特定字符。
    
    :param length: 字符串总长度，默认14
    :param max_digits: 允许的最大数字个数，默认4
    :param exclude_chars: 需要排除的字符字符串，默认排除易混淆的 0, O, 1, I
    :return: 随机生成的字符串
    """
    
    # --- 新增步骤：构建可用的字符池 ---
    # 将排除字符串转换为集合(set)，提高查找效率
    exclude_set = set(exclude_chars)
    
    # 从标准库中过滤掉不需要的字符
    # 如果 exclude_chars 为空，则保持原样
    available_digits = "".join([d for d in string.digits if d not in exclude_set])
    available_letters = "".join([c for c in string.ascii_uppercase if c not in exclude_set])
    
    # 安全检查：防止排除太多导致字符池为空
    if not available_digits or not available_letters:
        raise ValueError("排除的字符太多，导致没有足够的数字或字母可供生成！")

    # 1. 随机决定这次要放几个数字 (0 到 max_digits 之间)
    digit_count = random.randint(0, max_digits)

    # 2. 计算需要多少个大写字母
    letter_count = length - digit_count

    # 3. 生成对应数量的数字和大写字母
    # 【修改点】这里使用过滤后的 available_digits 和 available_letters
    digits = random.choices(available_digits, k=digit_count)
    letters = random.choices(available_letters, k=letter_count)

    # 4. 合并列表并打乱顺序
    result_list = digits + letters
    random.shuffle(result_list)

    # 5. 拼接成字符串返回
    return ''.join(result_list)