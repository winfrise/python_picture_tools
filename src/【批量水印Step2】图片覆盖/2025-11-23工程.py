from image_overlay import process_single, process_batch

# 单文件处理
# image_path = ""
# overlay_image_path = ""
# output_path = ""
# process_single(
#     image_path=image_path,
#     overlay_image_path=overlay_image_path,
#     output_path=output_path
# )

# 批量处理-竖版
input_dir = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/竖版图片_统一尺寸"
output_dir = f"{input_dir}_加水印模板"
overlay_image_path = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/模板/水印_竖版.png"
process_batch(
    input_dir=input_dir,
    output_dir=output_dir,
    overlay_image_path=overlay_image_path
)

# 批量处理-横版
# input_dir = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/002_横版_竖版_分类/横版图片_统一尺寸"
# output_dir = f"{input_dir}_加水印模板"
# overlay_image_path = "/Volumes/西数4T外置/百度网盘默认下载/1111111111111111111/模板/水印_横版.png"
# process_batch(
#     input_dir=input_dir,
#     output_dir=output_dir,
#     overlay_image_path=overlay_image_path
# )
