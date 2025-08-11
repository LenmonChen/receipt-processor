from sqlalchemy import Column, String, Integer, ForeignKey, Enum, TIMESTAMP, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types import JSONType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from app.core.config import settings
from .session import Base
import datetime


class Bill(Base):
    """单据主表模型"""
    __tablename__ = "bills"

    id = Column(String(36), primary_key=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    # attachments = relationship("Attachment", back_populates="bill")

class Attachment(Base):
    """单据附件表模型"""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(String(36), ForeignKey('bills.id'), nullable=False)
    file_name = Column(String(255))
    file_type = Column(Enum("pdf", "jpg", "png", "jpeg", name="file_types"))
    content = Column(Text)  # 存储Base64或文件路径

    # bill = relationship("Bill", back_populates="attachments")
    # parsing_result = relationship("ParsingResult", uselist=False, back_populates="attachment")


class ParsingResult(Base):
    """AI解析结果表模型"""
    __tablename__ = "attach_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    head_id = Column(String(20), ForeignKey('attachments.id'), unique=True)
    file_name = Column(String(200))
    decoded_info = Column(JSONType)
    create_time = Column(TIMESTAMP, default=datetime.datetime.now)
    # # 使用AES加密存储敏感结果数据
    # result = Column(
    #     EncryptedType(JSONType, settings.DB_ENCRYPT_KEY, AesEngine, 'pkcs5')
    # )
    # status = Column(Enum('pending', 'success', 'failed', name='status_enum'))
    # error_message = Column(String(255))
    # created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    # updated_at = Column(TIMESTAMP, onupdate=datetime.datetime.utcnow)
    #
    # attachment = relationship("Attachment", back_populates="parsing_result")

