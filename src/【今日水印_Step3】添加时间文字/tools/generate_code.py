import random
import string
def generate_custom_code(length=14, max_digits=4):
    """
    生成指定长度的随机字符串（大写字母+数字），且数字个数不超过 max_digits。
    
    :param length: 字符串总长度，默认14
    :param max_digits: 允许的最大数字个数，默认4
    :return: 随机生成的字符串
    """
    # 1. 随机决定这次要放几个数字（0 到 max_digits 之间）
    digit_count = random.randint(0, max_digits)
    
    # 2. 计算需要多少个大写字母
    letter_count = length - digit_count
    
    # 3. 生成对应数量的数字和大写字母
    # string.digits 是 '0123456789'
    # string.ascii_uppercase 是 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = random.choices(string.digits, k=digit_count)
    letters = random.choices(string.ascii_uppercase, k=letter_count)
    
    # 4. 合并列表并打乱顺序（这一步很关键，保证数字位置随机）
    result_list = digits + letters
    random.shuffle(result_list)
    
    # 5. 拼接成字符串返回
    return ''.join(result_list)