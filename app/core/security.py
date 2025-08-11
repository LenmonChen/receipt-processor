import os
from fastapi import HTTPException, Depends, Header
import secrets
from app.core.config import settings


async def validateapikey(authorization: str = Header(...,  alias="Authorization")):
    print(f"收到的 Authorization 头: {authorization}")  # 调试
    return authorization
    """API密钥认证中间件"""
    # try:
    #     scheme, api_key = authorization.split()
    #     if scheme.lower() != "bearer":
    #         raise ValueError()
    #
    #     if not secrets.compare_digest(api_key, settings.API_ACCESS_KEY):
    #         raise HTTPException(
    #             status_code=403,
    #             detail="Invalid API Key",
    #             headers={"WWW-Authenticate": "Bearer"},
    #         )
    #
    #     return api_key
    # except (ValueError, AttributeError):
    #     raise HTTPException(
    #         status_code=401,
    #         detail="Invalid authentication credentials",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )


# 简易版无Bearer前缀的验证(可选)
def validate_simple_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if not secrets.compare_digest(api_key, settings.API_ACCESS_KEY):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
