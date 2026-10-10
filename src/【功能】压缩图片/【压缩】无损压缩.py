
if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/未命名文件夹 2/001/义乌市北遴电子商务商行欧盟授权代表续费（产品组）协议2026.10.20-2027.10.19__提取的图片"

    if os.path.isfile(input_path):
        output_path = None
        trimage_compress(
            input_path=input_path,
            output_path=output_path,
        )
    elif os.path.isdir(input_path):
        counter = [0]
        def callback_func(input_file, output_file):
            counter[0] += 1
            print(f"正在压缩第{counter[0]}张图片")
            trimage_compress(
                input_path=input_file,
                output_path=output_file,
            )

        input_dir = input_path
        output_dir = f"{input_dir}_无损压缩"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else:
        print(f"地址无效: {input_path}")