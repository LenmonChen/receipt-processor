from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.responses import JSONResponse

from app.api.v1.endpoints import parsing
from app.core.config import settings
from app.db.session import engine, Base
from contextlib import asynccontextmanager
from celery_app import celery_app

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # 启动逻辑
    print("Starting up...")
    # 例如初始化数据库连接
    yield
    # 关闭逻辑
    print("Shutting down...")
    # 例如关闭数据库连接池
app = FastAPI(
    title="单据附件解析API",
    description="解析发票/行程单/水单等财务单据的API服务",
    version="1.0.0",
    openapi_url="/openapi.json",
    lifespan=app_lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],
)
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com", "https://app.example.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,  # 如果需要 Cookie/认证
)
CORSMiddleware 是一个用于处理 CORS（跨域资源共享，Cross-Origin Resource Sharing） 的中间件。它的作用是允许或限制不同源（域名、协议、端口）的客户端访问你的 API，从而解决浏览器因安全策略而阻止跨域请求的问题
不仅仅是这几个参数,还可以设置别的
"""
# 创建数据库表（生产环境使用迁移工具）
# @app.on_event("startup")
# async def startup():
#     Base.metadata.create_all(bind=engine)
# main.py (片段)


"""
代码功能
Base.metadata.create_all(bind=engine) 会检查数据库中是否已存在与SQLAlchemy ORM模型定义（Base的子类）对应的表。如果不存在，则会自动创建这些表。

执行逻辑分解
触发时机：
@app.on_event("startup") 是FastAPI提供的事件钩子，表示当应用启动时执行。
因此每次FastAPI服务启动（或重启）时都会运行该方法。
对象解析：
Base：这是在db/session.py中通过declarative_base()创建的基类，所有ORM模型（如Bill、Attachment）都继承自这个基类。
Base.metadata：包含所有继承Base的模型类的元数据（如表名、列定义等）。
engine：SQLAlchemy的数据库引擎，在db/session.py初始化。
操作说明：
create_all(bind=engine)遍历Base.metadata中注册的所有Table对象（即每个ORM类对应的表结构），按照模型定义生成CREATE TABLE语句。
该操作只在表不存在时创建，不会删除或修改已有的表结构。
"""
# 包含路由
app.include_router(parsing.router, prefix="/api/v1/parsing", tags=["单据解析"])
# 注册路由, 假如不仅仅有"解析", 可以再注册其它的路由。比如注册用户相关的路由 app.include_router(users.router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """详细的请求验证错误显示"""
    print(f"422错误详细信息: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
