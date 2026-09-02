# 基于Python实现的PDF工具

- Pillow


```
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活环境 (Windows)
source venv/bin/activate

# 安装 Pillow（图片处理）
pip install Pillow

# 安装 opencv
pip install opencv-python

# 导出依赖列表
pip freeze > requirements.txt
```


重新修改一下代码，(1)增加保存图片的路径，如果保存文件的地址不存在，默认是输入图片所在的文件夹，文件名是[原文件名]_output.[原格式](2)增加调试代码，在参数中增加debug参数，如果debug参数为True，那么保存每一步的图片，图片地址和输入图片地址逻辑类似