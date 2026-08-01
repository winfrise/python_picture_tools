import os

def batch_process_file_with_callback(input_dir, output_dir,  callback_func,  **kwargs):

    # 1. 公共逻辑：校验目录是否存在
    if not os.path.isdir(input_dir):
        print(f"错误：路径不存在 -> {input_dir}")
        return
    
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')

    if not output_dir:
        output_dir = input_dir + "_output"

    if output_dir != 'NOT_SAVE':
        os.makedirs(output_dir, exist_ok=True)

    print(f"开始扫描目录: {input_dir} -> {output_dir}")
    
    # 2. 公共逻辑：遍历目录结构
    for dirpath, dirnames, filenames in os.walk(input_dir):
        print(f"📂 正在进入目录: {dirpath}") 
        for filename in filenames:

            if filename.lower().endswith(valid_extensions) and not filename.startswith('.'):
                # 构建原图和目标图的完整路径
                full_input_file = os.path.join(dirpath, filename)

                full_output_file = ""
                if output_dir != 'NOT_SAVE':
                    # 计算当前遍历到的文件夹相对于 input_dir 的路径
                    relative_path = os.path.relpath(full_input_file, input_dir)

                    # 拼接出目标文件夹的完整路径
                    full_output_file = os.path.join(output_dir, relative_path)

                try:
                    callback_func(
                        input_file = full_input_file, 
                        output_file = full_output_file, 
                        **kwargs
                    )
                except Exception as e:
                    print(f"处理文件失败 [{full_input_file}]: {e}")
               



