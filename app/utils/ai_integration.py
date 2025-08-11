import requests
import os
import time
import hashlib
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def call_qwen_api(file_data: bytes, model: str, api_key: str) -> dict:
    """
    调用阿里云Qwen文档解析API
    实际API参数需参考阿里云官方文档
    """
    # 基础配置
    endpoint_map = {
        "qwen-invoice": "https://dashscope.aliyuncs.com/api/v1/services/document-invoice/parse",
        "qwen-invoice_v2": "https://dashscope.aliyuncs.com/api/v1/services/document-invoice/v2/parse",
        "qwen-finance": "https://dashscope.aliyuncs.com/api/v1/services/document-finance/parse"
    }

    endpoint = endpoint_map.get(model, endpoint_map["qwen-finance"])

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-DashScope-Async": "enable"  # 要求异步处理
    }

    # 构建请求负载
    payload = {"file": ("document", file_data)}

    try:
        # 调用第一阶段的解析API
        start_time = time.time()
        response = requests.post(
            endpoint,
            files=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            raise ConnectionError(f"API错误: {response.status_code} - {response.text}")

        task_id = response.json().get("task_id")
        if not task_id:
            raise ValueError("API响应缺少task_id")

        logger.info(f"初始请求成功，任务ID: {task_id}，耗时: {time.time() - start_time:.2f}s")

        # 轮询获取结果
        return poll_async_result(task_id, api_key, model)

    except requests.exceptions.RequestException as re:
        logger.error(f"请求异常: {str(re)}")
        raise


def poll_async_result(task_id: str, api_key: str, model: str, retries=10, delay=3) -> dict:
    """轮询异步结果"""
    result_endpoint = "https://dashscope.aliyuncs.com/api/v1/tasks/" + task_id

    for attempt in range(retries):
        time.sleep(delay)
        try:
            response = requests.get(
                result_endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15
            )

            resp_data = response.json()
            status = resp_data.get("status")

            if status == "SUCCESS":
                logger.info(f"任务完成: {task_id}，尝试次数: {attempt + 1}")
                return resp_data["result"]
            elif status in ["PENDING", "RUNNING"]:
                logger.debug(f"任务处理中 [{status}]...")
                continue
            elif status == "FAILED":
                error_msg = resp_data.get("reason", "未知错误")
                logger.error(f"任务失败: {task_id} - {error_msg}")
                raise RuntimeError(f"云服务失败: {error_msg}")

        except requests.exceptions.RequestException as re:
            logger.warning(f"结果查询失败({attempt + 1}/{retries}): {str(re)}")

    raise TimeoutError("异步结果获取超时")
