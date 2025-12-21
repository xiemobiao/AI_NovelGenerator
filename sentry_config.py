"""
Sentry错误追踪和性能监控配置

提供完整的错误追踪、性能监控和用户反馈功能
"""
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

# Sentry配置
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SENTRY_RELEASE = os.getenv("SENTRY_RELEASE", "ai-novel-generator@1.0.0")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))  # 10%采样
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))  # 10%采样


def init_sentry():
    """
    初始化Sentry

    环境变量配置:
        SENTRY_DSN: Sentry项目DSN
        ENVIRONMENT: 环境名称 (development/staging/production)
        SENTRY_RELEASE: 版本号
        SENTRY_TRACES_SAMPLE_RATE: 性能追踪采样率 (0.0-1.0)
        SENTRY_PROFILES_SAMPLE_RATE: 性能分析采样率 (0.0-1.0)
    """
    if not SENTRY_DSN:
        logging.warning("SENTRY_DSN未配置，Sentry监控未启用")
        return

    # 日志集成配置
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # 捕获INFO及以上级别的日志
        event_level=logging.ERROR  # 将ERROR及以上级别作为事件发送
    )

    # 初始化Sentry
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        release=SENTRY_RELEASE,

        # 集成配置
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),  # FastAPI集成
            SqlalchemyIntegration(),  # SQLAlchemy集成
            RedisIntegration(),  # Redis集成
            CeleryIntegration(),  # Celery集成
            logging_integration,  # 日志集成
        ],

        # 性能监控配置
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,  # 追踪采样率
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,  # 性能分析采样率

        # 发送默认PII（个人身份信息）
        send_default_pii=False,  # 生产环境建议False

        # 附加标签
        attach_stacktrace=True,  # 附加堆栈跟踪

        # 请求体大小限制
        max_request_body_size="medium",  # small/medium/large/always

        # 面包屑配置
        max_breadcrumbs=50,  # 最多保留50个面包屑

        # 钩子函数
        before_send=before_send_hook,
        before_breadcrumb=before_breadcrumb_hook,
    )

    logging.info(f"✅ Sentry已初始化 (环境: {SENTRY_ENVIRONMENT}, 版本: {SENTRY_RELEASE})")


def before_send_hook(event, hint):
    """
    发送事件前的钩子函数

    可以在这里过滤、修改或丢弃事件

    Args:
        event: Sentry事件
        hint: 包含原始异常的字典

    Returns:
        修改后的event或None（丢弃事件）
    """
    # 过滤特定异常
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # 不发送404错误
        if exc_type.__name__ == "HTTPException" and hasattr(exc_value, "status_code"):
            if exc_value.status_code == 404:
                return None

        # 不发送用户取消的请求
        if exc_type.__name__ == "CancelledError":
            return None

    # 添加自定义标签
    event.setdefault("tags", {})
    event["tags"]["app_component"] = "novel-generator"

    # 添加额外上下文
    event.setdefault("contexts", {})
    event["contexts"]["runtime"] = {
        "name": "Python",
        "version": os.sys.version
    }

    return event


def before_breadcrumb_hook(crumb, hint):
    """
    添加面包屑前的钩子函数

    Args:
        crumb: 面包屑数据
        hint: 额外信息

    Returns:
        修改后的crumb或None（丢弃面包屑）
    """
    # 过滤敏感信息
    if crumb.get("category") == "query":
        # 不记录包含密码的SQL查询
        if "password" in crumb.get("message", "").lower():
            return None

    return crumb


def capture_exception_with_context(exception, **context):
    """
    捕获异常并添加额外上下文

    Args:
        exception: 异常对象
        **context: 额外的上下文信息

    Example:
        try:
            risky_operation()
        except Exception as e:
            capture_exception_with_context(
                e,
                user_id=123,
                project_id=456,
                operation="generate_novel"
            )
    """
    with sentry_sdk.push_scope() as scope:
        # 添加额外上下文
        for key, value in context.items():
            scope.set_context(key, {"value": value})

        # 捕获异常
        sentry_sdk.capture_exception(exception)


def capture_message_with_context(message, level="info", **context):
    """
    捕获消息并添加额外上下文

    Args:
        message: 消息内容
        level: 日志级别 (debug/info/warning/error/fatal)
        **context: 额外的上下文信息

    Example:
        capture_message_with_context(
            "用户完成小说生成",
            level="info",
            user_id=123,
            chapters=10
        )
    """
    with sentry_sdk.push_scope() as scope:
        # 设置级别
        scope.level = level

        # 添加额外上下文
        for key, value in context.items():
            scope.set_tag(key, value)

        # 捕获消息
        sentry_sdk.capture_message(message)


def set_user_context(user_id, username=None, email=None, **extra):
    """
    设置用户上下文

    Args:
        user_id: 用户ID
        username: 用户名（可选）
        email: 邮箱（可选）
        **extra: 额外的用户信息
    """
    sentry_sdk.set_user({
        "id": user_id,
        "username": username,
        "email": email,
        **extra
    })


def clear_user_context():
    """清除用户上下文"""
    sentry_sdk.set_user(None)


def add_breadcrumb(message, category="default", level="info", **data):
    """
    添加面包屑（用于追踪用户操作路径）

    Args:
        message: 面包屑消息
        category: 类别
        level: 级别
        **data: 额外数据

    Example:
        add_breadcrumb(
            "用户开始生成小说",
            category="user_action",
            level="info",
            project_id=123
        )
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data
    )


def start_transaction(name, op="task"):
    """
    开始性能追踪事务

    Args:
        name: 事务名称
        op: 操作类型 (task/http/db/cache)

    Returns:
        Transaction对象

    Example:
        with start_transaction("generate_novel", op="task") as transaction:
            # 执行耗时操作
            generate_novel()
    """
    return sentry_sdk.start_transaction(name=name, op=op)


def start_span(description, op="function"):
    """
    开始性能追踪Span

    Args:
        description: Span描述
        op: 操作类型

    Returns:
        Span对象

    Example:
        with start_span("查询用户数据", op="db.query") as span:
            user = db.query(User).first()
    """
    return sentry_sdk.start_span(description=description, op=op)


# 装饰器：自动追踪函数性能
def trace_function(op="function"):
    """
    装饰器：自动追踪函数性能

    Args:
        op: 操作类型

    Example:
        @trace_function(op="ai.generate")
        def generate_chapter(chapter_num):
            # AI生成逻辑
            pass
    """
    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            with start_span(description=func.__name__, op=op):
                return func(*args, **kwargs)

        return wrapper
    return decorator


# 装饰器：捕获函数异常
def capture_errors(extra_context=None):
    """
    装饰器：自动捕获函数异常

    Args:
        extra_context: 额外上下文函数

    Example:
        @capture_errors(extra_context=lambda args, kwargs: {"user_id": args[0]})
        def risky_operation(user_id):
            # 可能失败的操作
            pass
    """
    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {}
                if extra_context:
                    context = extra_context(args, kwargs)

                capture_exception_with_context(e, **context)
                raise

        return wrapper
    return decorator


# 性能监控辅助函数
class PerformanceMonitor:
    """性能监控上下文管理器"""

    def __init__(self, name, op="task", **tags):
        self.name = name
        self.op = op
        self.tags = tags
        self.transaction = None

    def __enter__(self):
        self.transaction = sentry_sdk.start_transaction(name=self.name, op=self.op)
        self.transaction.__enter__()

        # 设置标签
        for key, value in self.tags.items():
            self.transaction.set_tag(key, value)

        return self.transaction

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # 记录异常
            sentry_sdk.capture_exception(exc_val)

        self.transaction.__exit__(exc_type, exc_val, exc_tb)


if __name__ == "__main__":
    # 测试Sentry配置
    print("Sentry配置测试")
    print(f"DSN配置: {'✅ 已配置' if SENTRY_DSN else '❌ 未配置'}")
    print(f"环境: {SENTRY_ENVIRONMENT}")
    print(f"版本: {SENTRY_RELEASE}")
    print(f"追踪采样率: {SENTRY_TRACES_SAMPLE_RATE * 100}%")

    if SENTRY_DSN:
        init_sentry()
        print("\n发送测试事件...")
        capture_message_with_context("Sentry配置测试", level="info", test=True)
        print("✅ 测试完成，请在Sentry控制台查看")
