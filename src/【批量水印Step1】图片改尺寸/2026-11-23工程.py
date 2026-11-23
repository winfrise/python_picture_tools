from image_resize import process_single_image, process_batch_images

def get_target_size(w, h):
    """横版 -> (1430, 1280)，竖版 -> (1279, 2155)"""
    if w >= h: # 横版
        return 1430, 1280
    return 1279, 2155


if __name__ == "__main__":
    # 单文件
    # input_path = ""
    # output_path = ""
    # target_size_func = get_target_size
    # process_single_image(
    #     input_path=input_path,
    #     output_path=output_path,
    #     target_size_func=target_size_func,
    #     suffix="_改尺寸",
    # )

    # 批量
    input_dir = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/横版图片"
    output_dir = f"{input_dir}_统一尺寸"
    target_size_func=get_target_size
    process_batch_images(
        input_dir=input_dir,
        output_dir=output_dir,
        target_size_func=get_target_size,
    )

    # 批量
    input_dir = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/竖版图片"
    output_dir = f"{input_dir}_统一尺寸"
    target_size_func=get_target_size
    process_batch_images(
        input_dir=input_dir,
        output_dir=output_dir,
        target_size_func=get_target_size,
    )