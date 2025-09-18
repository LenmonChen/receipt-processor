import base64
import io
import logging
import imghdr
import os
from PIL import Image
import filetype  # 纯 Python 的替代方案
from app.core.config import settings
from mimetypes import MimeTypes
import re
from celery_app import celery_app

logger = logging.getLogger(__name__)


# def decode_base64(base64_str: str, encoding="utf-8") -> bytes:
#     """解码Base64字符串为二进制数据"""
#     try:
#         # 检查是否为标准的Base64格式
#         if "," in base64_str:
#             _, encoded = base64_str.split(",", 1)
#         else:
#             encoded = base64_str
#         return base64.b64decode(encoded)
#     except Exception as e:
#         logger.error(f"Base64解码失败: {str(e)}")
#         raise ValueError("无效的Base64格式")

@celery_app.task
def detect_mime_type(data: bytes) -> str:
    """通过内容检测MIME类型（纯Python实现）"""
    # 1. 先尝试用标准库检测图片
    image_type = detect_image_type(data)
    if image_type:
        return f"image/{image_type}"

    # 2. 使用纯Python的filetype库
    kind = filetype.guess(data)
    if kind:
        return kind.mime

    # 3. 自定义检测PDF
    if is_pdf(data):
        return "application/pdf"

    logger.warning("无法识别文件类型")
    return settings.FileType.UNKNOWN

@celery_app.task
def detect_image_type(data: bytes) -> str | None:
    """使用标准库检测图片类型"""
    try:
        # 检查常见图片格式
        image_type = imghdr.what(None, h=data)
        if image_type:
            # 标准化一些格式名称
            return "jpeg" if image_type == "jpg" else image_type
    except Exception as e:
        logger.error(f"图片类型检测失败: {str(e)}")
    return None

@celery_app.task
def is_pdf(data: bytes) -> bool:
    """检测是否为PDF文件"""
    return len(data) > 4 and data[:4] == b"%PDF"

@celery_app.task
def validate_file_type(data: bytes, allowed_types=settings.ALLOWED_FILE_TYPES) -> str:
    """验证文件实际类型"""
    mime_type = detect_mime_type(data)
    if mime_type not in allowed_types:
        raise ValueError(f"禁止的文件类型: {mime_type}")
    return mime_type

@celery_app.task
def get_file_extension(mime_type: str) -> str:
    """从MIME类型获取扩展名"""
    extension_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/bmp": "bmp",
        "image/tiff": "tiff",
        "application/pdf": "pdf",
        "image/webp": "webp",  # 添加更多支持的类型
    }
    return extension_map.get(mime_type, "unrecognized")





# 把base64的字符串转成文件
@celery_app.task
def base64_to_file(base64_str, filename=None):
    # 检查是否是Data URI格式（如"data:image/png;base64,..."）
    if base64_str.startswith('data:'):
        # 提取元数据和主体数据
        header, base64_str = base64_str.split(',', 1)

        # 尝试从header解析MIME类型
        mime_type = re.search(r'data:([^;]+)', header)
        ext = '.bin'  # 默认后缀

        # 使用MIME类型猜测文件后缀
        if mime_type:
            mime = MimeTypes()
            ext = mime.guess_extension(mime_type.group(1)) or '.bin'

        # 如果没有指定文件名，生成带后缀的随机文件名
        if filename is None:
            import time
            filename = f"file_{int(time.time())}{ext}"

    # 处理纯Base64字符串（非Data URI）
    else:
        if filename is None:
            filename = "output.bin"  # 默认文件名

    # Base64解码（自动处理填充）
    file_data = base64.b64decode(base64_str)

    file_root = os.path.join(os.getcwd(), 'temp') #创建一个临时的文件夹
    os.makedirs(file_root, exist_ok=True)
    filename = os.path.join(file_root, filename)
    # 写入文件
    with open(filename, 'wb') as f:
        f.write(file_data)

    return filename

@celery_app.task
def file_to_base64(file_path):
    """将文件转换为 Base64 编码字符串"""
    with open(file_path, "rb") as file:
        # 读取文件内容并编码为 Base64
        encoded_bytes = base64.b64encode(file.read())
        # 将字节串转换为字符串（可选）
        encoded_str = encoded_bytes.decode('utf-8')
    return encoded_str

# def image_to_base64(image_path):
#     with Image.open(image_path) as img:
#         buffered = io.BytesIO()
#         img.save(buffered, format="PNG")  # 可以根据需要更改格式，如"JPEG"
#         img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
#     return img_str