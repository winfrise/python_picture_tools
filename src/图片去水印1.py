import cv2
import numpy as np
import os

# 支持的图片格式后缀
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

def method_numpy(input_path, output_path=None, black_point=60, contrast=1.5):
    """
    方法一：基于 NumPy 的手动映射去水印（类似 PS 色阶拉伸）
    支持单张处理和批量处理
    """
    # 1. 判断是单张文件还是文件夹
    if os.path.isfile(input_path):
        files = [input_path]
        is_batch = False
    elif os.path.isdir(input_path):
        if output_path is None:
            raise ValueError("批量处理必须指定输出文件夹路径 (output_path)")
        os.makedirs(output_path, exist_ok=True)
        files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.lower().endswith(VALID_EXTENSIONS)]
        is_batch = True
    else:
        print(f"[错误] 路径不存在: {input_path}")
        return

    # 2. 遍历处理
    for file_path in files:
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[警告] 无法读取图片，已跳过: {file_path}")
            continue

        # 核心处理逻辑：NumPy 手动映射
        processed_img = np.clip(img * contrast - black_point, 0, 255).astype(np.uint8)

        # 3. 决定保存路径
        if is_batch:
            save_path = os.path.join(output_path, f"numpy_{os.path.basename(file_path)}")
        else:
            save_path = output_path if output_path else f"numpy_{os.path.basename(file_path)}"

        cv2.imwrite(save_path, processed_img)
        print(f"[NumPy 成功] 已保存: {save_path}")


# ================= 运行测试 =================
if __name__ == "__main__":
    # --- 场景 1：处理单张图片 ---
    # method_numpy("test.jpg", "cleaned_test.jpg", black_point=70)
    # method_opencv("test.jpg", "cleaned_test.jpg", alpha=40)

    # --- 场景 2：批量处理文件夹 ---
    INPUT_FOLDER = "/Users/teacher/Desktop/完成/去水印/11__提取的图片-22"
    OUTPUT_FOLDER = "/Users/teacher/Desktop/完成/去水印/11__提取的图片-22-334"

    # 调用 NumPy 方法批量处理
    method_numpy(INPUT_FOLDER, OUTPUT_FOLDER, black_point=60, contrast=1.5)

