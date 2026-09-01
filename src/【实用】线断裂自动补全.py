import cv2
import numpy as np

def fix_broken_table_lines(input_path, output_path):
    # 1. 读取图片
    img = cv2.imread(input_path)
    if img is None:
        print("错误：无法找到图片")
        return

    # 2. 预处理：转灰度并二值化
    # 表格线通常是黑色的，背景是浅绿色。
    # THRESH_BINARY_INV 会将黑色线条变为白色(255)，背景变为黑色(0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

    # --- 第一步：提取水平线骨架 ---
    # 获取图片宽度，用于设定核的大小
    h, w = binary.shape[:2]
    # 定义一个“扁长”的核：宽度为图片宽度的1/30，高度固定为1
    # 这个操作会把断裂的水平线“吸”出来，同时过滤掉文字
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // 30, 1))
    horizontal_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

    # --- 第二步：提取垂直线骨架 ---
    # 定义一个“细长”的核：宽度固定为1，高度为图片高度的1/30
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, h // 30))
    vertical_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

    # --- 第三步：定向修补（关键步骤） ---
    # 我们只在提取出的“骨架”位置进行膨胀，这样就不会乱连文字
    
    # 修补水平线：用扁长的核膨胀，只填补左右断点
    # iterations=3 表示膨胀力度，根据断裂程度调整，太大容易变粗
    repaired_h = cv2.dilate(horizontal_mask, horizontal_kernel, iterations=3)
    
    # 修补垂直线：用细长的核膨胀，只填补上下断点
    repaired_v = cv2.dilate(vertical_mask, vertical_kernel, iterations=3)

    # --- 第四步：合并线条并叠加回原图 ---
    # 将修补好的横线和竖线合并
    final_lines_mask = cv2.bitwise_or(repaired_h, repaired_v)

    # 将线条颜色设为黑色 (0,0,0)
    # 利用掩码将原图中对应位置涂黑
    img[final_lines_mask == 255] = [0, 0, 0]

    # 保存结果
    cv2.imwrite(output_path, img)
    print(f"处理完成，已保存至: {output_path}")


# 调用示例（替换为你的图片路径）
if __name__ == "__main__":
    input_image = "/Users/teacher/Desktop/20260830/项目图片去水印定200/111/证书/test3/青岛大学_页面_034.jpg"   # 输入图片路径
    output_image = "repaired_table.png"  # 输出图片路径
    fix_broken_table_lines(input_image, output_image)