import glob
import os

from networkx.algorithms.operators.binary import compose

from app.models.schemas import ParsingRequest
import base64
import re
from app.utils.attach_process import process_image_txt, process_img_vl, get_file_id
from app.utils.file_processing import base64_to_file, file_to_base64
from app.db.models import ParsingResult
from app.db.session import get_db
from sqlalchemy.orm import Session
import json
import time
from app.tasks.split_images import split_imgs
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
        # filename = base64_to_file(attach, attachment.file_name) #考虑到CV库对于中文名的附件支持不够,直接用bill_id来命名
        composed_file_name = bill_id+'_'+str(int(time.time()))+'.'+filetype.lower()  #造了一个文件名,避免cv/PIL执行异常，编号+时间秒+文件类型
        filename = base64_to_file(attach, composed_file_name)
        attach_infos = []
        if is_valid_base64(attach): #是真实的有文件了
            if filetype.lower() in ('pdf', 'txt', 'docx', 'xlsx', 'csv'):  # 调用QWEN-LONG对应的模型
                file_id = get_file_id(filename)
                attach_info = process_image_txt(file_id)
                attach_infos.append(attach_info)
            else:
                # 针对非文档类的附件(图片性质)的, 首先做个判断,这个图片中的凭证信息是多个还是单独一个
                img_nums = split_imgs(filename) # img_nums 返回有多少个文件路径
                #调用Qwen的VL-MAX模型
                if img_nums == 'simple':
                    attach_info = process_img_vl(attach)
                    attach_infos.append(attach_info)
                else: # multiple多个凭证,集合在一个图片上
                    jpg_files = glob.glob(os.path.join(filename[:-4], "*.jpg")) # filename[:-4] 文件对应的文件夹路径
                    for jpg_file in jpg_files:
                        encoded_str = file_to_base64(jpg_file)
                        info = process_img_vl(encoded_str)
                        attach_infos.append(info)

        else:
            attach_info={'无效的附件':'无效的附件'}
            attach_infos.append(attach_info)
        for attach_info in attach_infos:
            attach_info = clean_and_parse_json(attach_info)
            db_attach_info = ParsingResult(
                    head_id=bill_id,
                    file_name=attachment.file_name,
                    decoded_info=attach_info
                )
            print(attach_info)
            db.add(db_attach_info)
        db.commit()
