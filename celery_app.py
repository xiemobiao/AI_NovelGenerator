"""
Celery异步任务队列配置

提供异步任务处理能力，用于小说生成、导出等耗时操作
"""
import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from datetime import timedelta

# Celery配置
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# 创建Celery应用
celery_app = Celery(
    "novel_generator",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks"]  # 导入任务模块
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 结果过期时间（1天）
    result_expires=60 * 60 * 24,

    # 任务结果配置
    result_extended=True,
    result_backend_transport_options={"master_name": "mymaster"},

    # 任务执行配置
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟硬超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # Worker丢失时拒绝任务

    # Worker配置
    worker_prefetch_multiplier=4,  # 预取任务数
    worker_max_tasks_per_child=1000,  # 每个worker子进程最多执行1000个任务后重启

    # 队列配置
    task_routes={
        "tasks.generate_novel_task": {"queue": "generation"},
        "tasks.export_novel_task": {"queue": "export"},
        "tasks.process_chapter_task": {"queue": "processing"},
        "tasks.cleanup_old_data_task": {"queue": "maintenance"},
    },

    # 定时任务配置
    beat_schedule={
        "cleanup-old-cache-every-hour": {
            "task": "tasks.cleanup_old_cache_task",
            "schedule": timedelta(hours=1),
        },
        "update-stats-every-30min": {
            "task": "tasks.update_global_stats_task",
            "schedule": timedelta(minutes=30),
        },
    },

    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# 任务信号处理
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """任务开始前的处理"""
    print(f"任务开始: {task.name} (ID: {task_id})")


@task_postrun.connect
def task_postrun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra
):
    """任务完成后的处理"""
    print(f"任务完成: {task.name} (ID: {task_id}, State: {state})")


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra
):
    """任务失败的处理"""
    print(f"任务失败: {sender.name} (ID: {task_id})")
    print(f"错误: {exception}")
    # 这里可以添加错误通知逻辑，如发送邮件、Slack通知等


if __name__ == "__main__":
    # 测试Celery配置
    print("Celery配置:")
    print(f"Broker: {CELERY_BROKER_URL}")
    print(f"Backend: {CELERY_RESULT_BACKEND}")
    print("\n队列配置:")
    for task, config in celery_app.conf.task_routes.items():
        print(f"  {task} -> {config['queue']}")
    print("\n定时任务:")
    for name, config in celery_app.conf.beat_schedule.items():
        print(f"  {name}: {config['task']} (每 {config['schedule']})")
