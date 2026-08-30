from find_exclusion_mask import find_exclusion_mask

if __name__ == "__main__":
    # 1. 排除区域代码调试
    image_path = "/Users/teacher/Desktop/test/test/page316_img1.png"
    debug_mode = True

    results = find_exclusion_mask(
        image_path = image_path,
        debug_mode = debug_mode,
    )
    
    if results:
        print(f"\n🎉 检测完成！共找到 {len(results)} 个区域。")
        for i, box in enumerate(results):
            print(f"区域 {i+1}: x={box[0]}, y={box[1]}, w={box[2]}, h={box[3]}")
    else:
        print("\n😭 未找到任何匹配区域。")
