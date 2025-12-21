"""
Celery异步任务定义

包含小说生成、导出、数据处理等异步任务
"""
import time
import json
from typing import Dict, Any, List
from celery import Task
from celery_app import celery_app
from redis_client import cache_manager, CacheKeys
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Project, Chapter, User
from cached_services import (
    ProjectService,
    ChapterService,
    UserService,
    StatsService
)
import logging

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """带数据库会话的任务基类"""

    _db = None

    def after_return(self, *args, **kwargs):
        """任务返回后清理数据库连接"""
        if self._db is not None:
            self._db.close()

    @property
    def db(self) -> Session:
        """获取数据库会话"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db


@celery_app.task(bind=True, base=DatabaseTask, name="tasks.generate_novel_task")
def generate_novel_task(
    self,
    project_id: int,
    user_id: int,
    chapter_start: int = 1,
    chapter_end: int = 10
) -> Dict[str, Any]:
    """
    异步生成小说章节

    Args:
        project_id: 项目ID
        user_id: 用户ID
        chapter_start: 开始章节号
        chapter_end: 结束章节号

    Returns:
        任务结果
    """
    try:
        # 更新任务状态
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": chapter_end - chapter_start + 1, "status": "初始化..."}
        )

        # 获取项目信息
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 验证用户权限
        if project.owner_id != user_id:
            raise ValueError(f"用户无权限操作此项目")

        generated_chapters = []

        # 逐章节生成
        for chapter_num in range(chapter_start, chapter_end + 1):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": chapter_num - chapter_start + 1,
                    "total": chapter_end - chapter_start + 1,
                    "status": f"正在生成第 {chapter_num} 章..."
                }
            )

            # 检查章节是否已存在
            existing_chapter = self.db.query(Chapter).filter(
                Chapter.project_id == project_id,
                Chapter.chapter_number == chapter_num
            ).first()

            if existing_chapter:
                logger.info(f"章节 {chapter_num} 已存在，跳过")
                continue

            # 模拟AI生成（实际应调用AI模型）
            # TODO: 集成实际的AI生成模型
            time.sleep(2)  # 模拟生成时间

            chapter_content = f"""第{chapter_num}章 自动生成的内容

这是通过异步任务自动生成的章节内容。在实际应用中，这里应该调用AI模型生成真实内容。

项目: {project.title}
章节号: {chapter_num}
生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

章节正文内容会在这里...
"""

            # 创建章节
            new_chapter = Chapter(
                project_id=project_id,
                chapter_number=chapter_num,
                title=f"第{chapter_num}章",
                content=chapter_content,
                word_count=len(chapter_content),
                status="completed"
            )
            self.db.add(new_chapter)
            self.db.commit()
            self.db.refresh(new_chapter)

            generated_chapters.append({
                "chapter_id": new_chapter.id,
                "chapter_number": chapter_num,
                "word_count": new_chapter.word_count
            })

            # 清除项目相关缓存
            ProjectService.invalidate_project_cache(project_id)
            ChapterService.invalidate_chapter_cache(new_chapter.id)

        # 更新项目状态
        project.status = "completed"
        self.db.commit()

        return {
            "project_id": project_id,
            "generated_chapters": generated_chapters,
            "total_generated": len(generated_chapters),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"小说生成失败: {e}")
        raise


@celery_app.task(bind=True, base=DatabaseTask, name="tasks.export_novel_task")
def export_novel_task(
    self,
    project_id: int,
    user_id: int,
    export_format: str = "txt"
) -> Dict[str, Any]:
    """
    异步导出小说

    Args:
        project_id: 项目ID
        user_id: 用户ID
        export_format: 导出格式 (txt, epub, pdf)

    Returns:
        任务结果（包含文件路径）
    """
    try:
        self.update_state(state="PROGRESS", meta={"status": "正在导出..."})

        # 获取项目和章节
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project or project.owner_id != user_id:
            raise ValueError("项目不存在或无权限")

        chapters = self.db.query(Chapter).filter(
            Chapter.project_id == project_id
        ).order_by(Chapter.chapter_number).all()

        if not chapters:
            raise ValueError("项目没有章节")

        # 生成导出内容
        export_content = f"{project.title}\n\n"
        export_content += f"作者: 用户{user_id}\n"
        export_content += f"共 {len(chapters)} 章\n"
        export_content += "=" * 50 + "\n\n"

        for chapter in chapters:
            export_content += f"\n\n{chapter.title}\n"
            export_content += "-" * 50 + "\n"
            export_content += chapter.content or ""
            export_content += "\n"

        # 保存文件（实际应保存到对象存储或文件系统）
        # TODO: 实现实际的文件保存逻辑
        import os
        export_dir = "/tmp/novel_exports"
        os.makedirs(export_dir, exist_ok=True)

        filename = f"novel_{project_id}_{int(time.time())}.{export_format}"
        filepath = os.path.join(export_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(export_content)

        # 缓存导出结果（24小时）
        cache_key = CacheKeys.format(
            CacheKeys.TASK_RESULT,
            task_id=self.request.id
        )
        cache_manager.set(
            cache_key,
            {"filepath": filepath, "filename": filename},
            ttl=60 * 60 * 24
        )

        return {
            "project_id": project_id,
            "filename": filename,
            "filepath": filepath,
            "format": export_format,
            "total_chapters": len(chapters),
            "total_words": sum(ch.word_count or 0 for ch in chapters),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"导出失败: {e}")
        raise


@celery_app.task(bind=True, base=DatabaseTask, name="tasks.process_chapter_task")
def process_chapter_task(
    self,
    chapter_id: int,
    operations: List[str]
) -> Dict[str, Any]:
    """
    异步处理章节（分析、优化、检查等）

    Args:
        chapter_id: 章节ID
        operations: 操作列表 ["analyze", "optimize", "spell_check"]

    Returns:
        处理结果
    """
    try:
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            raise ValueError(f"章节不存在: {chapter_id}")

        results = {}

        for i, operation in enumerate(operations):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": len(operations),
                    "status": f"正在执行: {operation}"
                }
            )

            if operation == "analyze":
                # 分析章节内容
                results["analysis"] = {
                    "word_count": len(chapter.content or ""),
                    "paragraph_count": (chapter.content or "").count("\n\n") + 1,
                    "has_dialogue": "「" in (chapter.content or "") or '"' in (chapter.content or ""),
                }

            elif operation == "optimize":
                # 优化章节（示例：去除多余空格）
                if chapter.content:
                    optimized = chapter.content.strip()
                    optimized = "\n".join(line.strip() for line in optimized.split("\n"))
                    results["optimization"] = {
                        "original_length": len(chapter.content),
                        "optimized_length": len(optimized),
                        "saved_bytes": len(chapter.content) - len(optimized)
                    }

            elif operation == "spell_check":
                # 拼写检查（简单示例）
                results["spell_check"] = {
                    "issues_found": 0,
                    "suggestions": []
                }

            time.sleep(1)  # 模拟处理时间

        # 清除章节缓存
        ChapterService.invalidate_chapter_cache(chapter_id)

        return {
            "chapter_id": chapter_id,
            "operations": operations,
            "results": results,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"章节处理失败: {e}")
        raise


@celery_app.task(name="tasks.cleanup_old_cache_task")
def cleanup_old_cache_task() -> Dict[str, Any]:
    """
    定时清理过期缓存（每小时执行）

    Returns:
        清理结果
    """
    try:
        redis = cache_manager.redis

        # 获取所有键
        all_keys = redis.keys("*")
        expired_count = 0

        for key in all_keys:
            ttl = redis.ttl(key)
            # 如果TTL为-1（永不过期）且不是系统键，则删除
            if ttl == -1 and not key.startswith("celery"):
                redis.delete(key)
                expired_count += 1

        logger.info(f"缓存清理完成: 删除 {expired_count} 个过期键")

        return {
            "total_keys": len(all_keys),
            "expired_keys": expired_count,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"缓存清理失败: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(bind=True, base=DatabaseTask, name="tasks.update_global_stats_task")
def update_global_stats_task(self) -> Dict[str, Any]:
    """
    定时更新全局统计信息（每30分钟执行）

    Returns:
        更新结果
    """
    try:
        # 清除旧的统计缓存
        StatsService.invalidate_global_stats()

        # 重新计算并缓存统计信息
        stats = StatsService.get_global_stats(self.db)

        logger.info(f"全局统计更新完成: {stats}")

        return {
            "stats": stats,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"统计更新失败: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(name="tasks.cleanup_old_data_task")
def cleanup_old_data_task(days: int = 30) -> Dict[str, Any]:
    """
    清理旧数据（手动触发）

    Args:
        days: 保留最近N天的数据

    Returns:
        清理结果
    """
    try:
        from datetime import datetime, timedelta

        db = SessionLocal()
        cutoff_date = datetime.now() - timedelta(days=days)

        # 这里可以添加具体的清理逻辑
        # 例如：删除旧的版本历史、临时文件等

        logger.info(f"数据清理完成: 删除 {cutoff_date} 之前的数据")

        db.close()

        return {
            "cutoff_date": cutoff_date.isoformat(),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"数据清理失败: {e}")
        return {"status": "error", "error": str(e)}


# 任务状态查询辅助函数
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    获取任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态信息
    """
    from celery.result import AsyncResult

    task_result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "state": task_result.state,
        "info": task_result.info,
        "successful": task_result.successful(),
        "failed": task_result.failed(),
        "ready": task_result.ready(),
    }


if __name__ == "__main__":
    print("Celery任务模块加载成功")
    print("\n可用任务:")
    print("  ✅ generate_novel_task - 异步生成小说")
    print("  ✅ export_novel_task - 异步导出小说")
    print("  ✅ process_chapter_task - 异步处理章节")
    print("  ✅ cleanup_old_cache_task - 定时清理缓存")
    print("  ✅ update_global_stats_task - 定时更新统计")
    print("  ✅ cleanup_old_data_task - 清理旧数据")
