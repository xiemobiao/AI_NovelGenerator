"""
数据库读写分离配置

提供主从数据库配置和自动路由功能
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# 数据库连接配置
DATABASE_WRITE_URL = os.getenv(
    "DATABASE_WRITE_URL",
    "postgresql://novelgen:password@database-master:5432/novel_generator"
)

DATABASE_READ_URL = os.getenv(
    "DATABASE_READ_URL",
    "postgresql://novelgen:password@database-replica:5432/novel_generator"
)

# 是否启用读写分离
READ_WRITE_SPLIT_ENABLED = os.getenv("READ_WRITE_SPLIT_ENABLED", "false").lower() == "true"

# 连接池配置
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "40"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

Base = declarative_base()


class DatabaseRouter:
    """数据库读写分离路由器"""

    def __init__(self):
        """初始化主从数据库引擎"""
        # 主库引擎（写入）
        self.write_engine = create_engine(
            DATABASE_WRITE_URL,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            pool_pre_ping=True,  # 连接前测试
            echo=False,
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000"  # 30秒查询超时
            }
        )

        # 从库引擎（读取）
        if READ_WRITE_SPLIT_ENABLED:
            self.read_engine = create_engine(
                DATABASE_READ_URL,
                pool_size=POOL_SIZE * 2,  # 读库连接池更大
                max_overflow=MAX_OVERFLOW * 2,
                pool_timeout=POOL_TIMEOUT,
                pool_recycle=POOL_RECYCLE,
                pool_pre_ping=True,
                echo=False,
                connect_args={
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=30000"
                }
            )
            logger.info("✅ 数据库读写分离已启用")
        else:
            self.read_engine = self.write_engine
            logger.info("ℹ️ 数据库读写分离未启用，使用单库模式")

        # 创建会话工厂
        self.WriteSession = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.write_engine
        )

        self.ReadSession = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.read_engine
        )

        # 设置事件监听
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """设置数据库事件监听器"""

        # 连接池checkout事件
        @event.listens_for(self.write_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("主库连接已建立")

        if READ_WRITE_SPLIT_ENABLED:
            @event.listens_for(self.read_engine, "connect")
            def receive_connect_read(dbapi_conn, connection_record):
                logger.debug("从库连接已建立")

        # 慢查询日志
        @event.listens_for(self.write_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            import time
            conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(self.write_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            import time
            if conn.info.get('query_start_time'):
                total = time.time() - conn.info['query_start_time'].pop(-1)
                if total > 1.0:  # 超过1秒记录慢查询
                    logger.warning(f"慢查询 ({total:.2f}s): {statement[:200]}")

    def get_write_session(self) -> Session:
        """获取写会话（连接主库）"""
        return self.WriteSession()

    def get_read_session(self) -> Session:
        """获取读会话（连接从库）"""
        return self.ReadSession()

    def init_db(self):
        """初始化数据库表（仅在主库执行）"""
        Base.metadata.create_all(bind=self.write_engine)
        logger.info("✅ 数据库表初始化完成")


# 全局数据库路由器实例
db_router = DatabaseRouter()


def get_write_db() -> Generator[Session, None, None]:
    """
    获取写数据库会话（FastAPI依赖注入用）

    用于：INSERT, UPDATE, DELETE操作

    Example:
        @app.post("/api/v1/users")
        def create_user(db: Session = Depends(get_write_db)):
            user = User(username="test")
            db.add(user)
            db.commit()
    """
    db = db_router.get_write_session()
    try:
        yield db
    finally:
        db.close()


def get_read_db() -> Generator[Session, None, None]:
    """
    获取读数据库会话（FastAPI依赖注入用）

    用于：SELECT操作

    Example:
        @app.get("/api/v1/users")
        def list_users(db: Session = Depends(get_read_db)):
            users = db.query(User).all()
            return users
    """
    db = db_router.get_read_session()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    db_router.init_db()


# 上下文管理器
class WriteDBContext:
    """写数据库上下文管理器"""

    def __enter__(self) -> Session:
        self.db = db_router.get_write_session()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.db.commit()
        else:
            self.db.rollback()
        self.db.close()


class ReadDBContext:
    """读数据库上下文管理器"""

    def __enter__(self) -> Session:
        self.db = db_router.get_read_session()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


# 装饰器：自动选择读写数据库
def use_write_db(func):
    """
    装饰器：使用写数据库

    Example:
        @use_write_db
        def create_user(username):
            # db会话会自动注入
            pass
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        with WriteDBContext() as db:
            # 将db注入到kwargs
            kwargs['db'] = db
            return func(*args, **kwargs)

    return wrapper


def use_read_db(func):
    """
    装饰器：使用读数据库

    Example:
        @use_read_db
        def get_users():
            # db会话会自动注入
            pass
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        with ReadDBContext() as db:
            # 将db注入到kwargs
            kwargs['db'] = db
            return func(*args, **kwargs)

    return wrapper


# 数据库健康检查
def check_database_health() -> dict:
    """
    检查数据库健康状态

    Returns:
        dict: 健康状态信息
    """
    result = {
        "write_db": "unknown",
        "read_db": "unknown",
        "write_pool": {},
        "read_pool": {}
    }

    try:
        # 检查写库
        with WriteDBContext() as db:
            db.execute("SELECT 1")
            result["write_db"] = "healthy"

            # 获取连接池状态
            result["write_pool"] = {
                "size": db_router.write_engine.pool.size(),
                "checked_out": db_router.write_engine.pool.checkedout(),
                "overflow": db_router.write_engine.pool.overflow(),
            }
    except Exception as e:
        result["write_db"] = f"error: {str(e)}"
        logger.error(f"写库健康检查失败: {e}")

    try:
        # 检查读库
        with ReadDBContext() as db:
            db.execute("SELECT 1")
            result["read_db"] = "healthy"

            # 获取连接池状态
            result["read_pool"] = {
                "size": db_router.read_engine.pool.size(),
                "checked_out": db_router.read_engine.pool.checkedout(),
                "overflow": db_router.read_engine.pool.overflow(),
            }
    except Exception as e:
        result["read_db"] = f"error: {str(e)}"
        logger.error(f"读库健康检查失败: {e}")

    return result


# 数据库统计信息
def get_database_stats() -> dict:
    """
    获取数据库统计信息

    Returns:
        dict: 统计信息
    """
    stats = {
        "read_write_split_enabled": READ_WRITE_SPLIT_ENABLED,
        "write_url": DATABASE_WRITE_URL.split("@")[-1],  # 隐藏密码
        "read_url": DATABASE_READ_URL.split("@")[-1],  # 隐藏密码
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
    }

    # 添加连接池状态
    health = check_database_health()
    stats.update({
        "write_pool_status": health["write_pool"],
        "read_pool_status": health["read_pool"],
    })

    return stats


if __name__ == "__main__":
    # 测试数据库配置
    print("=" * 60)
    print("数据库读写分离配置测试")
    print("=" * 60)

    stats = get_database_stats()
    print(f"\n读写分离状态: {'✅ 已启用' if stats['read_write_split_enabled'] else '❌ 未启用'}")
    print(f"写库地址: {stats['write_url']}")
    print(f"读库地址: {stats['read_url']}")
    print(f"连接池大小: {stats['pool_size']}")
    print(f"最大溢出: {stats['max_overflow']}")

    print("\n健康检查:")
    health = check_database_health()
    print(f"写库状态: {health['write_db']}")
    print(f"读库状态: {health['read_db']}")

    if health['write_pool']:
        print(f"\n写库连接池:")
        print(f"  - 大小: {health['write_pool']['size']}")
        print(f"  - 已使用: {health['write_pool']['checked_out']}")
        print(f"  - 溢出: {health['write_pool']['overflow']}")

    if health['read_pool']:
        print(f"\n读库连接池:")
        print(f"  - 大小: {health['read_pool']['size']}")
        print(f"  - 已使用: {health['read_pool']['checked_out']}")
        print(f"  - 溢出: {health['read_pool']['overflow']}")

    print("\n" + "=" * 60)
