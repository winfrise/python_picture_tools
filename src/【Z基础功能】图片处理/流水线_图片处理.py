from PIL import Image, ImageDraw
import os
import sys

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 计算父级目录（假设utils在src目录下，即当前目录的上一级）
parent_dir = os.path.dirname(current_dir)
# 将父级目录加入模块搜索路径
sys.path.append(parent_dir)

from utils import batch_process_file_with_callback

def process_image_actions(image_path, output_path, action_factory):
    """
    根据动作列表对图片进行处理并保存。
    
    :param image_path: 原始图片地址
    :param output_path: 处理后的图片输出地址
    :param actions: 动作列表，每个元素是一个字典，包含 'type' 和对应参数
    """
    try:
        img = Image.open(image_path).convert("RGBA")  # 转为 RGBA 以支持透明填充
    except Exception as e:
        print(f"打开图片失败: {e}")
        return

    actions = action_factory(image_path)
    for action in actions:
        action_type = action.get("type")

        # 动作 1: 水平移动 (正数向右，负数向左)
        if action_type == "move_horizontal":
            dx = action.get("distance", 0)
            # 创建一个与原图同样大小的透明背景
            new_img = Image.new("RGBA", img.size, (255, 255, 255))
            # 将原图粘贴到新背景上，实现移动效果（超出部分会被裁掉）
            new_img.paste(img, (dx, 0))
            img = new_img
            print(f"[执行] 水平移动: {dx}px")

        # 动作 2: 裁剪上下左右
        elif action_type == "crop":
            left = action.get("left", 0)
            top = action.get("top", 0)
            right = action.get("right", 0)
            bottom = action.get("bottom", 0)
            
            # 计算裁剪后的实际坐标 (相对于原图尺寸)
            crop_box = (left, top, img.width - right, img.height - bottom)
            
            # 边界安全检查
            if crop_box[0] < 0 or crop_box[1] < 0 or crop_box[2] > img.width or crop_box[3] > img.height:
                print(f"[警告] 裁剪区域 {crop_box} 超出图片边界，已自动修正")
                crop_box = (
                    max(0, crop_box[0]),
                    max(0, crop_box[1]),
                    min(img.width, crop_box[2]),
                    min(img.height, crop_box[3])
                )
                
            img = img.crop(crop_box)
            print(f"[执行] 裁剪: 左{left}, 上{top}, 右{right}, 下{bottom}")

        # 动作 3: 填充某个区域
        elif action_type == "fill":
            x = action.get("x", 0)
            y = action.get("y", 0)
            width = action.get("width", 0)
            height = action.get("height", 0)
            color = action.get("color", (255, 0, 0, 255))  # 默认红色，支持 RGBA
            
            draw = ImageDraw.Draw(img)
            draw.rectangle([x, y, x + width, y + height], fill=color)
            print(f"[执行] 填充区域: 位置({x},{y}), 大小({width}x{height}), 颜色{color}")

        else:
            print(f"[未知动作] 跳过: {action_type}")

    # 保存结果 (如果是 RGBA 且输出为 jpg，需要转回 RGB)
    if output_path.lower().endswith(('.jpg', '.jpeg')) and img.mode == 'RGBA':
        img = img.convert("RGB")
        
    img.save(output_path)
    print(f"[完成] 图片已保存至: {output_path}")


# ================= 测试用例 =================
if __name__ == "__main__":
    # 定义动作列表
    def my_actions (image_path):
        return [
            # 3. 在 (50, 50) 的位置，填充一个 100x100 的半透明蓝色矩形
            {
                "type": "fill", 
                "x": 3573, "y": 391,
                "width": 362, "height": 5365, 
                "color": (255, 255, 255)
            },

            # 1. 向右移动 50 像素
            {
                "type": "move_horizontal", 
                "distance": 181
            },
            
            # 2. 裁剪：左边裁掉 10px，上边裁掉 20px，右边裁掉 10px，下边裁掉 20px
            # {
            #     "type": "crop", 
            #     "left": 500, "top": 20, "right": 500, "bottom": 20
            # },
            

        ]
    image_path = "/Users/teacher/Desktop/不/111"

    if os.path.isfile(image_path):
        base_name, ext = os.path.splitext(image_path)
        output_path  = f"{base_name}_output{ext}"
        # 执行处理
        process_image_actions(
            image_path=image_path,      # 替换为你的输入图片路径
            output_path=output_path,    # 替换为你的输出图片路径
            action_factory=my_actions
        )
    elif os.path.isdir(image_path):
        def callback_func(input_file, output_file):
            process_image_actions(
                image_path=input_file,      # 替换为你的输入图片路径
                output_path=output_file,    # 替换为你的输出图片路径
                action_factory=my_actions
            )

        input_dir = image_path
        output_dir = f"{input_dir}_output_流水线"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func
        )

