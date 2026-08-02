import os
import math
from PIL import Image, ImageDraw, ImageFont

def add_precise_watermark(
    image_path, 
    output_path=None, 
    text="内部资料", 
    angle=45, 
    font_size=40, 
    color=(0, 0, 0),      # RGB颜色
    opacity=128,          # 透明度 0-255
    spacing=0             # 【关键】间距系数。0表示无缝拼接，>0表示增加间隙
):
    # 1. 路径处理
    if not output_path:
        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_output{ext}"

    print(f"正在处理: {os.path.basename(image_path)} | 角度: {angle}° | 间距系数: {spacing}")

    # 2. 打开原图
    base_image = Image.open(image_path).convert("RGBA")
    img_w, img_h = base_image.size
    
    # 3. 创建同尺寸透明图层
    watermark_layer = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark_layer)

    # 4. 加载字体并获取文字原始尺寸
    try:
        font_path = "/Users/teacher/Library/Fonts/SourceHanSerifSC-Bold.otf"
        font = ImageFont.truetype(font_path, font_size) # Windows常用黑体，Mac/Linux需改路径
    except IOError:
        font = ImageFont.load_default()
    
    # 获取文字的包围盒 (left, top, right, bottom)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]


    step_x = text_w + spacing
    step_y = text_h + spacing
    rotated_w = text_w
    rotated_h = text_h



    if angle % 360 != 0:
        # 5. 核心数学计算：计算旋转后的占用空间
        rad = math.radians(angle)
        cos_val = abs(math.cos(rad))
        sin_val = abs(math.sin(rad))

        # 旋转后的新宽高 (这是文字旋转后实际占据的矩形空间)
        rotated_w = int(text_w * cos_val + text_h * sin_val)
        rotated_h = int(text_w * sin_val + text_h * cos_val)

        # 6. 计算平铺步长 (支持 spacing=0)
        # 逻辑：基础步长是旋转后的尺寸，spacing 是额外的比例
        step_x = rotated_w + spacing
        step_y = rotated_h + spacing
        
    # 防止步长为0或负数导致死循环（极端情况保护）
    if step_x <= 0: step_x = text_w
    if step_y <= 0: step_y = text_h

    # 7. 开始平铺绘制
    # 关键点：从负坐标开始画，保证旋转中心对齐，解决边缘被切问题
    # 偏移量设为旋转后尺寸的一半
    start_x = -rotated_w // 2
    start_y = -rotated_h // 2
    
    # 循环范围要足够大，覆盖整个画布并多出边缘部分
    # x轴循环
    x = start_x
    while x < img_w + rotated_w:
        # y轴循环
        y = start_y
        while y < img_h + rotated_h:
            # 在 (x, y) 处绘制文字
            # 注意：这里直接画在透明层上，然后旋转整个层会更快，
            # 但为了精准控制每个文字的间距，我们采用“先画正字，再整体旋转”或者“逐个旋转绘制”。
            # 鉴于你要精确控制 spacing，**逐个绘制并旋转**是最稳妥的，虽然稍慢但不出错。
            
            # 方案优化：为了性能，我们通常创建一个单字的小图，旋转它，然后 paste 到大图。
            # 这里演示最稳健的“单字旋转粘贴法”：
            
            # A. 创建单字透明小图 (尺寸略大于文字以防切边)
            single_txt_img = Image.new('RGBA', (text_w, text_h), (255, 255, 255, 0))
            single_draw = ImageDraw.Draw(single_txt_img)
            
            # B. 在小图中心画正字
            
            # 绘制文字（需根据bbox微调居中）
            single_draw.text(
                (-text_bbox[0], -text_bbox[1]), 
                text, 
                font=font, 
                fill=(*color, opacity)
            )
            rotated_single = single_txt_img.rotate(angle, expand=True, resample=Image.BICUBIC)
        
            # D. 粘贴到水印层
            # 计算粘贴位置（需要补偿 small image 的 padding）
            paste_x = x + 1
            paste_y = y + 1
            
            watermark_layer.paste(rotated_single, (paste_x, paste_y), mask = rotated_single)

            y += step_y
        x += step_x

    # 8. 合并图层
    result = Image.alpha_composite(base_image, watermark_layer)
    
    # 9. 保存
    result_rgb = result.convert("RGB") # 转回RGB以便保存为jpg，如果是png可保留RGBA
    result_rgb.save(output_path)
    print(f"处理完成: {output_path}")

# --- 使用示例 ---
if __name__ == "__main__":
    IMAGE_PATH = "/Volumes/西数4T外置/拼多多图片/图文速改（通用详情页）/未命名文件夹/白鲨详情页.png" 
    OUTPUT_PATH = None
    TEXT = "白鲨图文快改"
    ANGLE = 45
    FONT_SIZE = 40
    COLOR = (0, 0, 0)      # RGB颜色
    OPACITY = 128          # 透明度 0-255
    SPACING = 20            # 【关键】间距系数。0表示无缝拼接，>0表示增加间隙

    # 假设你有一张 test.jpg
    # spacing=0 表示紧密排列
    add_precise_watermark( 
        image_path = IMAGE_PATH, 
        output_path = OUTPUT_PATH, 
        text = TEXT, 
        angle = ANGLE, 
        font_size = FONT_SIZE, 
        color = COLOR,      # RGB颜色
        opacity = OPACITY,          # 透明度 0-255
        spacing = SPACING             # 【关键】间距系数。0表示无缝拼接，>0表示增加间隙
    )