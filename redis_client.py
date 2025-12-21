"""
Redis缓存客户端和工具函数

提供Redis连接管理、缓存装饰器和常用缓存操作
"""
import json
import pickle
from functools import wraps
from typing import Any, Callable, Optional, Union
import redis
from redis.connection import ConnectionPool
import os
from datetime import timedelta

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DECODE_RESPONSES = True

# 缓存过期时间（秒）
CACHE_TTL_SHORT = 60 * 5  # 5分钟
CACHE_TTL_MEDIUM = 60 * 30  # 30分钟
CACHE_TTL_LONG = 60 * 60 * 2  # 2小时
CACHE_TTL_VERY_LONG = 60 * 60 * 24  # 24小时


class RedisClient:
    """Redis客户端封装类"""

    _instance = None
    _pool = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化Redis连接池"""
        if self._pool is None:
            self._pool = ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=REDIS_DECODE_RESPONSES,
                max_connections=50,
                socket_timeout=5,
                socket_connect_timeout=5,
            )

    def get_client(self) -> redis.Redis:
        """获取Redis客户端实例"""
        return redis.Redis(connection_pool=self._pool)

    def ping(self) -> bool:
        """测试Redis连接"""
        try:
            client = self.get_client()
            return client.ping()
        except Exception as e:
            print(f"Redis连接失败: {e}")
            return False


# 全局Redis客户端实例
redis_client = RedisClient()


def get_redis() -> redis.Redis:
    """获取Redis客户端（依赖注入用）"""
    return redis_client.get_client()


class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_client: redis.Redis = None):
        self.redis = redis_client or get_redis()

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            value = self.redis.get(key)
            if value is None:
                return default
            # 尝试JSON反序列化
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"Redis GET错误: {e}")
            return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """设置缓存值"""
        try:
            # 序列化值
            if serialize and not isinstance(value, (str, bytes)):
                value = json.dumps(value, ensure_ascii=False)

            if ttl:
                return self.redis.setex(key, ttl, value)
            else:
                return self.redis.set(key, value)
        except Exception as e:
            print(f"Redis SET错误: {e}")
            return False

    def delete(self, *keys: str) -> int:
        """删除缓存键"""
        try:
            return self.redis.delete(*keys)
        except Exception as e:
            print(f"Redis DELETE错误: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            print(f"Redis EXISTS错误: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        try:
            return self.redis.expire(key, seconds)
        except Exception as e:
            print(f"Redis EXPIRE错误: {e}")
            return False

    def ttl(self, key: str) -> int:
        """获取键剩余过期时间"""
        try:
            return self.redis.ttl(key)
        except Exception as e:
            print(f"Redis TTL错误: {e}")
            return -2

    def flush_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis FLUSH_PATTERN错误: {e}")
            return 0

    def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        try:
            return self.redis.incr(key, amount)
        except Exception as e:
            print(f"Redis INCR错误: {e}")
            return 0

    def decr(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        try:
            return self.redis.decr(key, amount)
        except Exception as e:
            print(f"Redis DECR错误: {e}")
            return 0


# 全局缓存管理器
cache_manager = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    parts = [str(arg) for arg in args]
    if kwargs:
        parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    return ":".join(parts)


def cached(
    ttl: int = CACHE_TTL_MEDIUM,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
        key_builder: 自定义键生成函数

    Example:
        @cached(ttl=300, key_prefix="user")
        def get_user(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_builder:
                cache_key_str = key_builder(*args, **kwargs)
            else:
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key_str = ":".join(key_parts)

            # 尝试从缓存获取
            cached_value = cache_manager.get(cache_key_str)
            if cached_value is not None:
                return cached_value

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            if result is not None:
                cache_manager.set(cache_key_str, result, ttl=ttl)

            return result

        # 添加缓存清除方法
        def clear_cache(*args, **kwargs):
            """清除特定参数的缓存"""
            if key_builder:
                cache_key_str = key_builder(*args, **kwargs)
            else:
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key_str = ":".join(key_parts)
            cache_manager.delete(cache_key_str)

        def clear_all_cache():
            """清除所有相关缓存"""
            pattern = f"{key_prefix or func.__name__}:*"
            cache_manager.flush_pattern(pattern)

        wrapper.clear_cache = clear_cache
        wrapper.clear_all_cache = clear_all_cache

        return wrapper
    return decorator


def invalidate_cache(*keys: str):
    """使缓存失效（删除）"""
    cache_manager.delete(*keys)


def invalidate_pattern(pattern: str):
    """使匹配模式的缓存失效"""
    cache_manager.flush_pattern(pattern)


# 常用缓存键名称空间
class CacheKeys:
    """缓存键命名空间"""

    # 用户相关
    USER_INFO = "user:info:{user_id}"
    USER_PROJECTS = "user:projects:{user_id}"
    USER_STATS = "user:stats:{user_id}"

    # 项目相关
    PROJECT_INFO = "project:info:{project_id}"
    PROJECT_CHAPTERS = "project:chapters:{project_id}"
    PROJECT_BLUEPRINT = "project:blueprint:{project_id}"

    # 章节相关
    CHAPTER_CONTENT = "chapter:content:{chapter_id}"
    CHAPTER_VERSIONS = "chapter:versions:{chapter_id}"

    # 任务相关
    TASK_STATUS = "task:status:{task_id}"
    TASK_RESULT = "task:result:{task_id}"

    # 统计相关
    STATS_DAILY = "stats:daily:{date}"
    STATS_USER_COUNT = "stats:user:count"
    STATS_PROJECT_COUNT = "stats:project:count"

    # 限流相关
    RATE_LIMIT = "ratelimit:{user_id}:{endpoint}"

    @classmethod
    def format(cls, template: str, **kwargs) -> str:
        """格式化缓存键"""
        return template.format(**kwargs)


# 速率限制装饰器
def rate_limit(
    max_requests: int = 10,
    window: int = 60,
    key_func: Optional[Callable] = None
):
    """
    速率限制装饰器

    Args:
        max_requests: 时间窗口内最大请求数
        window: 时间窗口（秒）
        key_func: 自定义键生成函数

    Example:
        @rate_limit(max_requests=5, window=60)
        async def generate_novel(user_id: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成限流键
            if key_func:
                limit_key = key_func(*args, **kwargs)
            else:
                limit_key = f"ratelimit:{func.__name__}:{args[0] if args else 'default'}"

            # 检查当前请求数
            current = cache_manager.incr(limit_key)

            if current == 1:
                # 第一个请求，设置过期时间
                cache_manager.expire(limit_key, window)

            if current > max_requests:
                # 超过限制
                ttl = cache_manager.ttl(limit_key)
                raise Exception(f"速率限制：请在 {ttl} 秒后重试")

            return func(*args, **kwargs)

        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试代码
    print("测试Redis连接...")
    if redis_client.ping():
        print("✅ Redis连接成功")

        # 测试基本操作
        print("\n测试基本缓存操作...")
        cache_manager.set("test_key", {"name": "测试", "value": 123}, ttl=60)
        result = cache_manager.get("test_key")
        print(f"缓存结果: {result}")

        # 测试装饰器
        print("\n测试缓存装饰器...")
        @cached(ttl=30, key_prefix="demo")
        def expensive_function(x: int, y: int):
            print(f"执行耗时函数: {x} + {y}")
            return x + y

        print(f"第一次调用: {expensive_function(1, 2)}")
        print(f"第二次调用（应该从缓存获取）: {expensive_function(1, 2)}")

        print("\n✅ 所有测试通过")
    else:
        print("❌ Redis连接失败")
