"""
Prometheus指标收集

为FastAPI应用提供详细的性能监控指标
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable
import psutil
import os

# ============ 应用信息 ============
app_info = Info("novel_generator_app", "AI Novel Generator Application Info")
app_info.info({
    "version": "1.0.0",
    "environment": os.getenv("ENVIRONMENT", "development")
})

# ============ HTTP请求指标 ============
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"]
)

# ============ 数据库指标 ============
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query latency in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections"
)

db_query_errors_total = Counter(
    "db_query_errors_total",
    "Total database query errors",
    ["operation", "table"]
)

# ============ Redis缓存指标 ============
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_key_prefix"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_key_prefix"]
)

cache_operations_duration_seconds = Histogram(
    "cache_operations_duration_seconds",
    "Cache operation latency in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1)
)

# ============ Celery任务指标 ============
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"]
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution time in seconds",
    ["task_name"],
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800)
)

celery_tasks_in_progress = Gauge(
    "celery_tasks_in_progress",
    "Number of Celery tasks in progress",
    ["task_name"]
)

# ============ 业务指标 ============
novel_generation_total = Counter(
    "novel_generation_total",
    "Total novel generation requests",
    ["status"]
)

novel_chapters_generated_total = Counter(
    "novel_chapters_generated_total",
    "Total chapters generated"
)

novel_words_generated_total = Counter(
    "novel_words_generated_total",
    "Total words generated"
)

novel_exports_total = Counter(
    "novel_exports_total",
    "Total novel exports",
    ["format", "status"]
)

user_registrations_total = Counter(
    "user_registrations_total",
    "Total user registrations"
)

user_logins_total = Counter(
    "user_logins_total",
    "Total user logins",
    ["status"]
)

active_users = Gauge(
    "active_users",
    "Number of currently active users"
)

active_projects = Gauge(
    "active_projects",
    "Number of active projects"
)

# ============ 系统资源指标 ============
system_cpu_usage = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage"
)

system_memory_usage = Gauge(
    "system_memory_usage_bytes",
    "System memory usage in bytes"
)

system_memory_available = Gauge(
    "system_memory_available_bytes",
    "System available memory in bytes"
)

system_disk_usage = Gauge(
    "system_disk_usage_bytes",
    "System disk usage in bytes",
    ["path"]
)

# ============ WebSocket指标 ============
websocket_connections_active = Gauge(
    "websocket_connections_active",
    "Number of active WebSocket connections"
)

websocket_messages_sent_total = Counter(
    "websocket_messages_sent_total",
    "Total WebSocket messages sent",
    ["message_type"]
)

websocket_messages_received_total = Counter(
    "websocket_messages_received_total",
    "Total WebSocket messages received",
    ["message_type"]
)


# ============ 装饰器 ============

def track_request_metrics(endpoint: str):
    """跟踪HTTP请求指标的装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = "GET"  # 默认，实际应从请求获取
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

            start_time = time.time()
            status = "200"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "500"
                raise
            finally:
                duration = time.time() - start_time

                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

                http_requests_in_progress.labels(
                    method=method,
                    endpoint=endpoint
                ).dec()

        return wrapper
    return decorator


def track_db_query(operation: str, table: str):
    """跟踪数据库查询指标的装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                db_query_errors_total.labels(
                    operation=operation,
                    table=table
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)

        return wrapper
    return decorator


def track_cache_operation(operation: str):
    """跟踪缓存操作指标的装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                cache_operations_duration_seconds.labels(
                    operation=operation
                ).observe(duration)

        return wrapper
    return decorator


# ============ 系统资源收集 ============

def collect_system_metrics():
    """收集系统资源指标"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_usage.set(cpu_percent)

        # 内存使用
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.used)
        system_memory_available.set(memory.available)

        # 磁盘使用
        disk = psutil.disk_usage('/')
        system_disk_usage.labels(path='/').set(disk.used)

    except Exception as e:
        print(f"系统指标收集失败: {e}")


# ============ 缓存指标辅助函数 ============

def record_cache_hit(cache_key_prefix: str):
    """记录缓存命中"""
    cache_hits_total.labels(cache_key_prefix=cache_key_prefix).inc()


def record_cache_miss(cache_key_prefix: str):
    """记录缓存未命中"""
    cache_misses_total.labels(cache_key_prefix=cache_key_prefix).inc()


# ============ 业务指标辅助函数 ============

def record_novel_generation(status: str, chapters: int = 0, words: int = 0):
    """记录小说生成"""
    novel_generation_total.labels(status=status).inc()
    if chapters > 0:
        novel_chapters_generated_total.inc(chapters)
    if words > 0:
        novel_words_generated_total.inc(words)


def record_novel_export(export_format: str, status: str):
    """记录小说导出"""
    novel_exports_total.labels(format=export_format, status=status).inc()


def record_user_registration():
    """记录用户注册"""
    user_registrations_total.inc()


def record_user_login(status: str):
    """记录用户登录"""
    user_logins_total.labels(status=status).inc()


def update_active_users(count: int):
    """更新活跃用户数"""
    active_users.set(count)


def update_active_projects(count: int):
    """更新活跃项目数"""
    active_projects.set(count)


# ============ Celery任务指标 ============

def record_celery_task_start(task_name: str):
    """记录Celery任务开始"""
    celery_tasks_in_progress.labels(task_name=task_name).inc()


def record_celery_task_end(task_name: str, status: str, duration: float):
    """记录Celery任务结束"""
    celery_tasks_total.labels(task_name=task_name, status=status).inc()
    celery_task_duration_seconds.labels(task_name=task_name).observe(duration)
    celery_tasks_in_progress.labels(task_name=task_name).dec()


# ============ WebSocket指标 ============

def record_websocket_connection(delta: int):
    """记录WebSocket连接变化"""
    if delta > 0:
        websocket_connections_active.inc(delta)
    else:
        websocket_connections_active.dec(-delta)


def record_websocket_message_sent(message_type: str):
    """记录WebSocket发送消息"""
    websocket_messages_sent_total.labels(message_type=message_type).inc()


def record_websocket_message_received(message_type: str):
    """记录WebSocket接收消息"""
    websocket_messages_received_total.labels(message_type=message_type).inc()


if __name__ == "__main__":
    print("Prometheus指标模块加载成功")
    print("\n可用指标:")
    print("  ✅ HTTP请求指标 (http_requests_total, http_request_duration_seconds)")
    print("  ✅ 数据库指标 (db_query_duration_seconds, db_connections_active)")
    print("  ✅ Redis缓存指标 (cache_hits_total, cache_misses_total)")
    print("  ✅ Celery任务指标 (celery_tasks_total, celery_task_duration_seconds)")
    print("  ✅ 业务指标 (novel_generation_total, user_registrations_total)")
    print("  ✅ 系统资源指标 (system_cpu_usage, system_memory_usage)")
    print("  ✅ WebSocket指标 (websocket_connections_active)")
