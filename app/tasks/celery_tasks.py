from celery import shared_task
import os
import logging
import time
from sqlalchemy.exc import SQLAlchemyError
from app.utils import ai_integration, file_processing
from app.db.session import SessionLocal
from app.db.models import Bill, Attachment, ParsingResult
from app.core.config import settings
from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, soft_time_limit=240)
def process_attachments_task(self, request_data: dict):
    """异步处理附件解析任务"""
    db = SessionLocal()
    bill_id = request_data["bill_id"]
    print(f"开始处理bill_id:{bill_id}...")
    try:
        # 1. 创建主单记录
        bill = Bill(id=bill_id)
        db.add(bill)
        db.flush()  # 获取新创建的bill ID而不提交事务

        # 2. 处理每个附件
        for attachment_data in request_data["attachments"]:
            file_name = attachment_data["file_name"]
            base64_content = attachment_data["content_base64"]
            print(base64_content)

            # 2.1 解码Base64并验证文件
            bin_data = file_processing.decode_base64(base64_content)

            # 2.2 检查实际文件类型(防欺骗)
            mime_type = file_processing.detect_mime_type(bin_data)
            file_ext = file_processing.get_file_extension(mime_type)

            if mime_type not in settings.ALLOWED_FILE_TYPES:
                raise ValueError(f"不支持的文件类型: {mime_type}")

            # 2.3 选择合适的Qwen模型
            # model_name = "qwen-invoice" if "invoice" in file_ext.lower() else "qwen-finance"
            model_name = "qwen-vl-ocr" if file_ext == 'pdf' else "qwen-vl-max"


            # 2.4 调用AI解析接口
            retry_count = 0
            success = False
            ai_response = None

            while retry_count < 3 and not success:
                try:
                    ai_response = ai_integration.call_qwen_api(
                        file_data=bin_data,
                        model=model_name,
                        api_key=settings.ALIYUN_API_KEY
                    )
                    success = True
                except Exception as api_error:
                    retry_count += 1
                    logger.error(f"阿里云API调用失败 ({retry_count}/3): {str(api_error)}")
                    time.sleep(2 ** retry_count)  # 指数退避

            if not success:
                raise RuntimeError("阿里云API调用失败超过最大重试次数3")

            # 2.5 保存附件记录
            attachment = Attachment(
                bill_id=bill.id,
                file_name=file_name,
                file_type=file_ext,
                content=base64_content if settings.DEBUG_MODE else None  # 生产环境不存原始内容
            )
            db.add(attachment)
            db.flush()

            # 2.6 保存解析结果
            result = ParsingResult(
                attachment_id=attachment.id,
                model_used=model_name,
                result=ai_response,
                status="success",
            )
            db.add(result)

        db.commit()

    except ValueError as ve:
        db.rollback()
        logger.error(f"数据处理错误: {str(ve)}")
        self.retry(exc=ve, countdown=60)
    except RuntimeError as ae:
        db.rollback()
        logger.error(f"AI处理错误: {str(ae)}")
        # 创建失败结果
        result = ParsingResult(
            attachment_id=attachment.id,
            model_used=model_name,
            result={"error": str(ae)},
            status="failed",
            error_message=str(ae)
        )
        db.add(result)
        db.commit()
    except SQLAlchemyError as se:
        db.rollback()
        logger.error(f"数据库错误: {str(se)}")
        self.retry(exc=se, countdown=60)
    except Exception as e:
        db.rollback()
        logger.exception("意外的处理错误")
        self.retry(exc=e, countdown=120, max_retries=1)
    finally:
        db.close()
