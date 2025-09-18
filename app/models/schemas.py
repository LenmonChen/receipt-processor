from pydantic import BaseModel, Field, validator, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from app.core.config import settings
from fastapi import Body,HTTPException
import base64
import binascii


class FileType(str, Enum):
    PDF = "application/pdf"
    JPEG = "image/jpeg"
    PNG = "image/png"
    UNKNOWN = "application/octet-stream"

# 这个模型类展示了如何结合Pydantic的类型系统和自定义验证器，构建一个安全可靠、文档友好并且高度可配置的API输入模型。
class AttachmentIn(BaseModel):
    """附件基类模型，接收Base64编码内容"""
    file_name: str = Field(..., example="invoice_001.pdf", max_length=255)  # Field(...)中的...：表示该字段是必填的(required)
    content_base64: str = Field(..., description="Base64编码的文件内容")

    @field_validator('content_base64')
    def validate_base64_size(cls, v):
        # Base64大小检验 (实际文件大小约为base64长度的3/4), 设置了20MB的限制
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        base64_size = len(v)
        if base64_size > (max_bytes * 4 / 3) * 1.1:  # 10%缓冲
            raise ValueError(f"文件大小超过{settings.MAX_FILE_SIZE_MB}MB限制")
        return v


class ParsingRequest(BaseModel):
    """单据解析请求模型"""
    bill_id: str = Field(..., min_length=5, max_length=100, example="INV-2024-001")
    attachments: List[AttachmentIn] = Field(..., min_items=1, description="单据关联的附件列表")


class ParsingResult(BaseModel):
    """解析结果模型"""
    model_used: str = Field(..., example="qwen-invoice")
    result: Dict[str, Any] = Field(..., example={"amount": 999.99, "vendor": "Example Corp"})
    status: str = Field(..., example="success")


class TaskResponse(BaseModel):
    """异步任务响应模型"""
    task_id: str
    status: str = "Processing started"
    detail: str = "任务已加入处理队列"
    endpoint: str = "/api/v1/task/status/{task_id}"



# --------- Base64 验证依赖项 -----------
def validate_request_and_attachments(
    request: ParsingRequest = Body(...)  # 先用 pydantic 检查结构
) -> ParsingRequest:
    for idx, attachment in enumerate(request.attachments):
        try:
            # 严格验证 base64 格式
            decoded_data = base64.b64decode(attachment.content_base64, validate=True)
            # 可选操作：进一步检查 decoded_data 是否为空等
        except binascii.Error:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Base64 string in attachment at index {idx}"
            )
    return request