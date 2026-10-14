import os, sys
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import batch_process_file_with_callback
from tools.compress_luban import luban_compress

if __name__ == "__main__":
    input_path = "/Volumes/西数4T外置/百度网盘默认下载/2M/001_output_jpg"
    
    # target_size_kb = 50

    total_size_kb = 2 * 1024
    total_page = 16
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