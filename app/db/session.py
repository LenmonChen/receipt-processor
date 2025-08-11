# 数据库连接
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(settings.DB_URL, pool_pre_ping=True, pool_recycle=3600)

# 会话工厂函数
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 依赖注入的数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db  ### 出现了生成器的概念
    finally:
        db.close()

