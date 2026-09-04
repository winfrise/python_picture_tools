# 纹理修复
import cv2
def perform_inpaint(img, mask, inpaint_radius=3, algo=cv2.INPAINT_TELEA):
    """
    执行 OpenCV Inpaint 纹理修复
    
    Args:
        img: 输入图像（已经是颜色填充后的图像）
        mask: 水印掩码（白色区域为需要修复的位置）
        inpaint_radius: 修复半径，越大平滑度越高，但可能模糊细节
        algo: 修复算法，cv2.INPAINT_TELEA（快速行进法）或 cv2.INPAINT_NS（流体动力学）
    
    Returns:
        修复后的图像
    """
    return cv2.inpaint(img, mask, inpaintRadius=inpaint_radius, flags=algo)