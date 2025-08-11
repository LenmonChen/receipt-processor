from app.models.schemas import ParsingRequest
import base64
import re
from app.utils.attach_process import process_image_txt, process_img_vl, get_file_id
from app.utils.file_processing import base64_to_file
from app.db.models import ParsingResult
from app.db.session import get_db
from sqlalchemy.orm import Session
import json

# 判断字符串是否为有效的文件
def is_valid_base64(s):
    if not isinstance(s, str):
        return False
    # Base64 字符串通常只包含 A-Z, a-z, 0-9, '+', '/', 并可能以 0, 1, 2, 3 个等号结尾
    pattern = re.compile(r'^[A-Za-z0-9+/]+={0,2}$')
    if not pattern.match(s):
        return False
    # 尝试解码，看是否成功
    try:
        decoded = base64.b64decode(s, validate=True)
        return True
    except:
        return False

def clean_and_parse_json(dirty_json_string):
    # 1. 去除前置和后置的非 JSON 内容（如代码块标记、换行）
    cleaned = re.sub(r'^```json\s*|\s*```$', '', dirty_json_string.strip())

    # 2. 尝试解析成 Python 字典
    try:
        parsed_json = json.loads(cleaned)
        return parsed_json
    except json.JSONDecodeError as e:
        print("JSON 解析失败，内容如下：")
        print(cleaned)
        raise e


# 用来处理具体的传输过来的文件
def deal_info(msg: ParsingRequest):
    bill_id = msg.bill_id
    bill_attach = msg.attachments
    db:Session = next(get_db())
    for attachment in bill_attach:
        attach = attachment.content_base64
        filetype = attachment.file_name.split('.')[-1] #得到对应的文件类型(pdf和img调用不同的模型)
        filename = base64_to_file(attach, attachment.file_name)
        if is_valid_base64(attach): #是真实的有文件了
            if filetype.lower() in ('pdf', 'txt', 'docx', 'xlsx', 'csv'):  # 调用QWEN-LONG对应的模型
                file_id = get_file_id(filename)
                attach_info = process_image_txt(file_id)
            else:
                #调用Qwen的VL-MAX模型
                attach_info = process_img_vl(attach)
        else:
            attach_info={'无效的附件':'无效的附件'}
        attach_info = clean_and_parse_json(attach_info)
        db_attach_info = ParsingResult(
                head_id=bill_id,
                file_name=filename,
                decoded_info=attach_info
            )
        print(attach_info)
        db.add(db_attach_info)
    db.commit()
