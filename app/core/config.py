# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import Optional
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv  # 添加此导入

# 确保加载环境变量 - 绝对路径到 .env 文件
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # 项目根目录
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

class Settings(BaseSettings):
    # ==== 必须添加以下数据库配置字段 ====
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: int = Field(3306, env="DB_PORT")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    DB_NAME: str = Field(..., env="DB_NAME")

    DB_ENCRYPT_KEY: str = Field(..., env="DB_ENCRYPT_KEY")
    # ==== 其他配置项保持原样 ====
    API_V1_STR: str = "/api/v1"
    ALLOWED_FILE_TYPES: list[str] = ["image/jpeg", "image/png", "application/pdf"]

    # CELERY_BROKER_URL: str = Field(..., env="CELERY_BROKER_URL")
    # CELERY_RESULT_BACKEND: str = Field(..., env="CELERY_RESULT_BACKEND")
    # ... 其他配置项 ...
    MAX_FILE_SIZE_MB: int = Field(..., env="MAX_FILE_SIZE_MB")

    API_ACCESS_KEY: str = Field(..., env="API_ACCESS_KEY")

    # 添加数据库连接字符串
    @property
    def DB_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        # case_sensitive = True  # 强制区分大小写
        env_file = ".env"  # 读取环境变量文件
        extra = "ignore"  # 忽略未声明但提供的额外字段


# 实例化配置
settings = Settings()
# print(settings.DB_NAME)