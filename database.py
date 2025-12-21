# database.py
# -*- coding: utf-8 -*-
"""
数据库配置和连接管理
使用SQLAlchemy ORM
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# 数据库URL配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./novel_generator.db"  # 默认使用SQLite
)

# 创建数据库引擎
# SQLite需要check_same_thread=False以支持多线程
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,  # 生产环境设为False，开发时可设为True查看SQL
    pool_pre_ping=True,  # 检查连接是否有效
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 声明基类
Base = declarative_base()


# 依赖注入：获取数据库会话
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI依赖项，提供数据库会话
    使用yield确保会话在请求结束后关闭
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 初始化数据库（创建所有表）
def init_db():
    """
    初始化数据库，创建所有表
    在应用启动时调用
    """
    from models import User, Project, Chapter, ChapterVersion  # 避免循环导入
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表已创建")


# 删除所有表（仅用于开发/测试）
def drop_db():
    """
    删除所有表
    警告: 仅用于开发环境，会删除所有数据！
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️ 数据库表已删除")
