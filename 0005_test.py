import cv2
import numpy as np
import os


def safe_imread(image_path):
    """更安全的图片读取函数"""
    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    # 检查文件权限
    if not os.access(image_path, os.R_OK):
        raise PermissionError(f"没有读取文件的权限: {image_path}")

    # 尝试多种方法读取
    try:
        # 方法1: 直接使用cv2.imread
        img = cv2.imread(image_path)
        if img is not None:
            return img
    except:
        pass

    try:
        # 方法2: 使用二进制读取并解码
        with open(image_path, 'rb') as f:
            img_bytes = np.frombuffer(f.read(), dtype=np.uint8)
            img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        if img is not None:
            return img
    except:
        pass

    try:
        # 方法3: 使用PIL后备方案
        from PIL import Image
        pil_img = Image.open(image_path)
        if pil_img.mode == 'RGBA':
            # 如果有alpha通道，转换为RGB
            pil_img = pil_img.convert('RGB')
        img_arr = np.array(pil_img)
        # 转换颜色空间: RGB to BGR
        img = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
        return img
    except Exception as e:
        raise RuntimeError(f"所有读取方法失败: {str(e)}")


# --------------- 处理发票公章 ----------------------
try:
    # 替换为你的实际路径
    image_path = r"C:\Users\13916\Desktop\2025财务管理课题\2025财务管理课题\附件\通行费\云南机打发票2.png"

    print("尝试读取图片...")
    image = safe_imread(image_path)
    print(f"图片读取成功! 尺寸: {image.shape}")

    # 图像增强
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)
    lab_eq = cv2.merge((l_eq, a, b))
    enhanced = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)

    # 尝试提取红色公章区域
    print("识别公章区域...")
    hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)

    # 定义红色范围 (调整这些值以匹配你的公章颜色)
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    # 优化公章蒙版
    mask = cv2.medianBlur(mask, 5)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)

    # 显示临时结果（调试用）
    cv2.imwrite("mask_before.png", mask)

    print("去除公章...")
    # 使用图像修复技术
    repaired = cv2.inpaint(enhanced, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

    # 保存结果
    output_path = "invoice_without_stamp.png"
    cv2.imwrite(output_path, repaired)
    print(f"处理完成! 结果已保存至: {output_path}")

except Exception as e:
    print(f"处理过程中出错: {str(e)}")
    # 如果需要更详细的错误信息：
    import traceback

    traceback.print_exc()
