from fastapi import APIRouter, Depends, HTTPException, status, Header, dependencies, HTTPException, Security, BackgroundTasks
from app.models.schemas import ParsingRequest, TaskResponse
from app.core.security import validateapikey
from app.tasks.celery_tasks import process_attachments_task
from app.db.session import get_db
from app.db.models import Bill
from celery.result import AsyncResult
import uuid
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.tasks.background_task import deal_info  # 具体处理附件的函数
import time
router = APIRouter()

# 1. 设置 Bearer Token 认证方案
security = HTTPBearer()



# 2. 修改你的 validateapikey 函数，改为 validate_token（更清晰的语义）
async def validate_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    print("收到的 Bearer Token:", token)
    if token != "valid-token":  # 你自己的校验逻辑
        raise HTTPException(status_code=403, detail="Invalid or missing token")
    return token

@router.post(
    "/parse",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="提交单据解析请求",
    dependencies=[Depends(validate_token)],
    description="接收单据ID和Base64附件列表，异步调用AI解析"
)
async def parse_document(
        request: ParsingRequest,  # 验证post过来的数据是否合理,不合理直接就raise 异常了;只有通过验证的数据才能执行下面的信息
        background_tasks: BackgroundTasks   #增加后台任务的方式, 测试情况下,就用这个。将来用redis
        # dependencies=[Depends(security.validateapikey)],
        # apikey: str = Depends(validate_token),
        # Depends(security.validateapikey),
        # db=Depends(get_db)
):
    # celery_task = process_attachments_task.delay(request.model_dump())  # delay() 是 Celery 中触发异步任务的核心方法，它将任务立即放入消息队列但不直接执行，让后台 worker 进程异步处理任务，调用方无需等待任务完成。
    background_tasks.add_task(deal_info, msg=request)
    return {
        "task_id": '111',
        "status": "Processing started",
        "detail": f"单据 '{request.bill_id}' 处理中",
        "endpoint": f"/api/v1/task/status/123"
    }

    # return {
    #     "task_id": str(celery_task.id),
    #     "status": "Processing started",
    #     "detail": f"单据 '{request.bill_id}' 处理中",
    #     "endpoint": f"/api/v1/task/status/{celery_task.id}"
    # }

"""
    # 检查单据ID是否已存在
    existing_bill = db.query(Bill).filter(Bill.id == request.bill_id).first()
    if existing_bill:
        raise HTTPException(
            status_code=400,
            detail=f"单据ID '{request.bill_id}' 已存在"
        )

    """
"""
    参数序列化：将 request.model_dump() 的结果转换为可序列化格式（JSON等）
    生成唯一ID：创建任务ID（如 c6b4b1ce-5ba7-4e50-8c8f-8d3d4f9b3f7b）
    发送消息：写入消息队列（默认使用RabbitMQ/Redis）
    返回句柄：创建 AsyncResult 对象但不阻塞当前线程

    # 使用apply_async的高级方式
    • 可设置复杂参数
    • 支持延迟执行
    • 可配置队列优先级
    process_attachments_task.apply_async(
        args=[request_data],
        queue='high_priority',
        countdown=10,  # 10秒后执行
        expires=120    # 2分钟未执行则自动过期
    )
    """



#
# @router.get(
#     "/task/status/{task_id}",
#     summary="查询任务状态",
#     description="通过任务ID查询异步处理状态"
# )
# async def check_task_status(task_id: str, api_key: str = Depends(security.validateapikey)):
#     """查询异步任务状态"""
#     task = AsyncResult(task_id)
#
#     response = {
#         "task_id": task_id,
#         "status": task.status,
#         "result": None,
#         "traceback": None
#     }
#
#     if task.status == "SUCCESS":
#         response["result"] = task.result
#     elif task.status == "FAILURE":
#         response["result"] = {"error": str(task.result)}
#         response["traceback"] = str(task.traceback)
#
#     return response
