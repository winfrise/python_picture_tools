if __name__ == "__main__":
    input_path = "/Users/teacher/Desktop/百度网盘下载/未命名文件夹 3/中华本草-苗药卷__提取的图片_鲁班压缩_output_滑块去水印"
    
    # target_size_kb = 50

    total_size_kb = 80 * 1024
    total_page = 664
    target_size_kb = math.floor(total_size_kb / total_page)
    print(f"target_size_kb: {target_size_kb}")



    if os.path.isfile(input_path):
        output_path = None
        luban_compress(
            input_path=input_path,
            output_path=output_path,
            target_size_kb=target_size_kb
        )
    elif os.path.isdir(input_path):
        counter = [0] 
        def callback_func(input_file, output_file):
            counter[0] += 1
            print(f"正在压缩第{counter[0]}张图片")
            luban_compress(
                input_path=input_file,
                output_path=output_file,
                target_size_kb=target_size_kb,
            )

        input_dir = input_path
        output_dir = f"{input_dir}_鲁班压缩"
        batch_process_file_with_callback(
            input_dir=input_dir,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else: 
         print(f"地址无效: {input_path}")