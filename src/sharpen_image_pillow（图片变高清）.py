from PIL import Image, ImageFilter

def sharpen_image(input_path, output_path):
    # 打开图片
    img = Image.open(input_path)
    
    # 应用 USM 锐化滤镜
    # radius: 锐化半径，通常为 2 左右
    # percent: 锐化强度，150% 表示增强程度
    # threshold: 阈值，控制多大程度的颜色差异才会被锐化，避免放大噪点
    sharpened_img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    # 保存处理后的图片
    sharpened_img.save(output_path)
    print(f"图片已锐化并保存至: {output_path}")

# 使用示例
sharpen_image("/Users/teacher/Desktop/《临床基础检验技术》复习要点/test/page4_img1.jpeg", "/Users/teacher/Desktop/《临床基础检验技术》复习要点/test/xxx2.jpeg")