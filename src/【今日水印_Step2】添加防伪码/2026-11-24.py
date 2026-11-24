from draw_code import draw_text_with_shadow, batch_draw_text_with_shadow
import os
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



def generate_text ():
    code = generate_custom_code()
    return f"防伪 {code}"

font_path = "/Users/teacher/Desktop/pdf_command/python_picture_tools/src/assets/fonts/苹方黑体-中粗-简.ttf"
text = generate_text

# 单张处理
# image = "/Volumes/西数4T外置/Chrome下载目录/美图设计室_11_24_2026/001_output/01.jpg"
# base_name, ext = os.path.splitext(image)
# output_path = f"{base_name}_o{ext}"
# draw_text_with_shadow(
#     image=image,
#     text="防伪 R9MA2BCBR4RCGY",
#     output_path=output_path,
#     x=-20, y=-10,        # 贴右下角
#     font_size=25,
#     font_color="white",
#     font_path=font_path,
#     shadow_offset=(0, 0), # 偏移量为0
#     shadow_blur=15,       # 模糊半径大 -> 产生光晕感
#     shadow_color=(0, 0, 0, 150) # 半透明黑阴影
# )

batch_draw_text_with_shadow(
    input_dir="/Volumes/西数4T外置/Chrome下载目录/美图设计室_11_24_2026/001_output",
    output_dir="/Volumes/西数4T外置/Chrome下载目录/美图设计室_11_24_2026/001_output2",
    text=text,                      # 此时该参数忽略
    use_filename_as_text=False,    # 开启将文件名作为文字
    text_prefix="",           # 在文件名前加 "SN: "
    x=-20, y=-10,                   # 左上角
    font_size=25,
    font_color="white",
    font_path=font_path,         # 微软雅黑
    shadow_color=(0, 0, 0, 200)
)