if __name__ == "__main__":

    def target_size_func (img_width, img_height):
        is_horizontal = img_width > img_height # 横向图片
        is_vertical = img_width < img_height  # 纵向图片
        if is_horizontal:
            return ['width', 100]
        return ['height', 100]

    INPUT_PATH = "/Users/teacher/Desktop/百度网盘下载/2M/扫描_压缩/教学工作1_扫描版__提取的图片"
    TARGET_SIZE = ['width', 700] # ['height', 300]或['width', 200] 
    # TARGET_SIZE = target_size_func


    if os.path.isfile(INPUT_PATH):
        input_path = INPUT_PATH

        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}_output_{TARGET_SIZE[0]}{TARGET_SIZE[1]}{ext}"
        resize_image(
            input_path=INPUT_PATH,
            output_path = output_path,
            target_size = TARGET_SIZE,
        )
    elif os.path.isdir(INPUT_PATH):
        def callback_func(input_path, output_path):
            resize_image(
                input_path=input_path,
                output_path= output_path,
                target_size = TARGET_SIZE,
            )
        input_dir = INPUT_PATH
        output_dir = f"{input_dir}_output_{TARGET_SIZE[0]}{TARGET_SIZE[1]}"
        batch_process_file_with_callback(
            input_dir=INPUT_PATH,
            output_dir=output_dir,
            callback_func=callback_func,
        )
    else: 
         print(f"地址无效: {INPUT_PATH}")