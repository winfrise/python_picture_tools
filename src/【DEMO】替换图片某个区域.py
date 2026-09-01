from PIL import Image
import numpy as np
import os


def process_image(target_path, mask_path, bg_path, text_path, output_path, threshold=128):
    print("🚀 开始处理图片...")
    
    # 1. 打开所有图片
    target_img = Image.open(target_path).convert("RGBA")
    mask_img = Image.open(mask_path).convert("L")  # 转为灰度图
    bg_img = Image.open(bg_path).convert("RGBA")
    text_img = Image.open(text_path).convert("RGBA")
    
    # ========== 【调试 1】打印所有图片的尺寸和模式 ==========
    print(f"📏 目标图片尺寸: {target_img.size}, 模式: {target_img.mode}")
    print(f"📏 选区图片尺寸: {mask_img.size}, 模式: {mask_img.mode}")
    print(f"📏 背景层尺寸: {bg_img.size}, 模式: {bg_img.mode}")
    print(f"📏 文字层尺寸: {text_img.size}, 模式: {text_img.mode}")
    # =======================================================
    
    # 确保尺寸一致
    base_size = target_img.size
    if mask_img.size != base_size or bg_img.size != base_size or text_img.size != base_size:
        print("⚠️ 警告: 图片尺寸不一致，正在强制缩放至目标图片尺寸...")
        mask_img = mask_img.resize(base_size, Image.Resampling.NEAREST)
        bg_img = bg_img.resize(base_size, Image.Resampling.LANCZOS)
        text_img = text_img.resize(base_size, Image.Resampling.LANCZOS)
        
    # 2. 处理选区图片，生成 Alpha 蒙版
    mask_array = np.array(mask_img)
    
    # ========== 【调试 2】检查选区黑白值分布 ==========
    white_pixels = np.sum(mask_array > threshold)
    black_pixels = np.sum(mask_array <= threshold)
    total_pixels = mask_array.size
    print(f"🔍 选区分析: 白色像素(选中区) = {white_pixels} ({white_pixels/total_pixels*100:.2f}%)")
    print(f"🔍 选区分析: 黑色像素(忽略区) = {black_pixels} ({black_pixels/total_pixels*100:.2f}%)")
    
    if white_pixels == 0:
        print("❌ 致命错误: 选区图片中没有任何像素超过阈值！请检查图片是否反色（白底黑字）或阈值过高！")
        return
    # ===================================================
    
    # binary_mask_array = np.where(mask_array > threshold, 255, 0).astype(np.uint8)
    inverted_array = np.where(mask_array < threshold, 255, 0).astype(np.uint8)
    alpha_mask = Image.fromarray(inverted_array, mode='L')


    
    
    # ========== 【调试 3】保存生成的纯蒙版图 ==========
    alpha_mask.save("debug_01_alpha_mask.png")
    print("💾 调试: 已保存纯蒙版图 -> debug_01_alpha_mask.png")
    # ===================================================
    
    # 3. 把背景层中选区对应的内容，替换到目标图片上
    target_img.paste(bg_img, (0, 0), alpha_mask)
    
    # ========== 【调试 4】保存贴完背景后的中间状态 ==========
    target_img.save("debug_02_after_bg_paste.png")
    print("💾 调试: 已保存替换背景后的状态 -> debug_02_after_bg_paste.png")
    # ===================================================
    
    # 4. 把文字层中选区对应的内容，覆盖在目标图片对应位置上


    # 1. 获取文字图层的灰度信息 (用于判断哪里是黑色)
    text_gray = text_img.convert('L')

    # 2. 生成“文字蒙版”：只保留黑色部分
    # 逻辑：像素值 < 100 (深色/黑色) -> 变 255 (选中)；否则变 0 (不选中)
    # 注意：这里把黑色变成了白色(选中)，是为了符合 paste 的规则
    text_mask = text_gray.point(lambda x: 255 if x < 100 else 0)

    # 3. 【关键步骤】合并两个蒙版
    # 使用 ImageChops.darker (取暗部) 或者 bitwise_and 逻辑
    # 只有当 alpha_mask (区域) 和 text_mask (文字) 都是白色时，结果才是白色
    from PIL import ImageChops
    final_mask = ImageChops.darker(alpha_mask, text_mask)

    # 4. 执行粘贴：使用合并后的最终蒙版
    target_img.paste(text_img, (0, 0), final_mask)

    
    # 5. 保存最终结果
    final_img = target_img.convert("RGB")
    final_img.save(output_path)
    print(f"✅ 处理完成，最终结果已保存至: {output_path}")

# ================= 使用示例 =================
if __name__ == "__main__":
    target_path="/Users/teacher/Desktop/20260830/项目图片去水印定金200/111/测试/页面_016.jpg"

    mask_path="/Users/teacher/Desktop/20260830/项目图片去水印定金200/111/测试/mask.png"       # 选区图片
    bg_path="/Users/teacher/Desktop/20260830/项目图片去水印定金200/111/测试/bg.png"   # 背景层
    text_path="/Users/teacher/Desktop/20260830/项目图片去水印定金200/111/测试/文字.jpg" # 文字层

    base_name, ext = os.path.splitext(target_path)
    output_path = f"{base_name}_output{ext}"
    process_image(
        target_path=target_path,   # 目标图片
        mask_path=mask_path,       # 选区图片
        bg_path=bg_path,   # 背景层
        text_path=text_path, # 文字层
        output_path=output_path    # 输出结果
    )