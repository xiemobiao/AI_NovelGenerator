"""
带缓存的服务层

为常用数据库查询操作提供缓存支持
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models import User, Project, Chapter, ChapterVersion
from redis_client import (
    cached,
    cache_manager,
    CacheKeys,
    CACHE_TTL_SHORT,
    CACHE_TTL_MEDIUM,
    CACHE_TTL_LONG,
    invalidate_pattern
)


class UserService:
    """用户服务（带缓存）"""

    @staticmethod
    @cached(ttl=CACHE_TTL_MEDIUM, key_prefix="user:info")
    def get_user_by_id(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户信息（缓存30分钟）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户信息字典或None
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value if hasattr(user.role, 'value') else user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        return None

    @staticmethod
    @cached(ttl=CACHE_TTL_MEDIUM, key_prefix="user:username")
    def get_user_by_username(db: Session, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息（通过用户名）"""
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value if hasattr(user.role, 'value') else user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        return None

    @staticmethod
    @cached(ttl=CACHE_TTL_SHORT, key_prefix="user:projects")
    def get_user_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取用户项目列表（缓存5分钟）

        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            项目列表
        """
        projects = db.query(Project).filter(
            Project.owner_id == user_id
        ).offset(skip).limit(limit).all()

        return [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in projects
        ]

    @staticmethod
    @cached(ttl=CACHE_TTL_LONG, key_prefix="user:stats")
    def get_user_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """
        获取用户统计信息（缓存2小时）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            统计信息字典
        """
        project_count = db.query(Project).filter(Project.owner_id == user_id).count()

        chapter_count = db.query(Chapter).join(Project).filter(
            Project.owner_id == user_id
        ).count()

        total_words = db.query(Chapter).join(Project).filter(
            Project.owner_id == user_id
        ).with_entities(Chapter.word_count).all()

        total_word_count = sum(wc[0] or 0 for wc in total_words)

        return {
            "project_count": project_count,
            "chapter_count": chapter_count,
            "total_word_count": total_word_count,
        }

    @staticmethod
    def invalidate_user_cache(user_id: int):
        """使用户相关缓存失效"""
        patterns = [
            f"user:info:{user_id}:*",
            f"user:projects:{user_id}:*",
            f"user:stats:{user_id}:*",
        ]
        for pattern in patterns:
            invalidate_pattern(pattern)


class ProjectService:
    """项目服务（带缓存）"""

    @staticmethod
    @cached(ttl=CACHE_TTL_MEDIUM, key_prefix="project:info")
    def get_project_by_id(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
        """
        获取项目信息（缓存30分钟）

        Args:
            db: 数据库会话
            project_id: 项目ID

        Returns:
            项目信息字典或None
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            return {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "status": project.status,
                "owner_id": project.owner_id,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            }
        return None

    @staticmethod
    @cached(ttl=CACHE_TTL_SHORT, key_prefix="project:chapters")
    def get_project_chapters(
        db: Session,
        project_id: int,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        获取项目章节列表（缓存5分钟）

        Args:
            db: 数据库会话
            project_id: 项目ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            章节列表
        """
        chapters = db.query(Chapter).filter(
            Chapter.project_id == project_id
        ).order_by(Chapter.chapter_number).offset(skip).limit(limit).all()

        return [
            {
                "id": ch.id,
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "content": ch.content[:200] + "..." if ch.content and len(ch.content) > 200 else ch.content,
                "word_count": ch.word_count,
                "status": ch.status,
                "created_at": ch.created_at.isoformat() if ch.created_at else None,
                "updated_at": ch.updated_at.isoformat() if ch.updated_at else None,
            }
            for ch in chapters
        ]

    @staticmethod
    @cached(ttl=CACHE_TTL_MEDIUM, key_prefix="project:blueprint")
    def get_project_blueprint(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目蓝图（缓存30分钟）"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if project and hasattr(project, 'blueprint'):
            return project.blueprint
        return None

    @staticmethod
    def invalidate_project_cache(project_id: int):
        """使项目相关缓存失效"""
        patterns = [
            f"project:info:{project_id}:*",
            f"project:chapters:{project_id}:*",
            f"project:blueprint:{project_id}:*",
        ]
        for pattern in patterns:
            invalidate_pattern(pattern)


class ChapterService:
    """章节服务（带缓存）"""

    @staticmethod
    @cached(ttl=CACHE_TTL_MEDIUM, key_prefix="chapter:content")
    def get_chapter_content(db: Session, chapter_id: int) -> Optional[Dict[str, Any]]:
        """
        获取章节内容（缓存30分钟）

        Args:
            db: 数据库会话
            chapter_id: 章节ID

        Returns:
            章节内容字典或None
        """
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            return {
                "id": chapter.id,
                "chapter_number": chapter.chapter_number,
                "title": chapter.title,
                "content": chapter.content,
                "word_count": chapter.word_count,
                "status": chapter.status,
                "project_id": chapter.project_id,
                "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
                "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None,
            }
        return None

    @staticmethod
    @cached(ttl=CACHE_TTL_MEDIUM, key_prefix="chapter:versions")
    def get_chapter_versions(
        db: Session,
        chapter_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取章节版本历史（缓存30分钟）

        Args:
            db: 数据库会话
            chapter_id: 章节ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            版本列表
        """
        versions = db.query(ChapterVersion).filter(
            ChapterVersion.chapter_id == chapter_id
        ).order_by(ChapterVersion.version_number.desc()).offset(skip).limit(limit).all()

        return [
            {
                "id": v.id,
                "version_number": v.version_number,
                "content": v.content[:200] + "..." if v.content and len(v.content) > 200 else v.content,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "created_by": v.created_by,
            }
            for v in versions
        ]

    @staticmethod
    def invalidate_chapter_cache(chapter_id: int):
        """使章节相关缓存失效"""
        patterns = [
            f"chapter:content:{chapter_id}:*",
            f"chapter:versions:{chapter_id}:*",
        ]
        for pattern in patterns:
            invalidate_pattern(pattern)


class StatsService:
    """统计服务（带缓存）"""

    @staticmethod
    @cached(ttl=CACHE_TTL_LONG, key_prefix="stats:global")
    def get_global_stats(db: Session) -> Dict[str, Any]:
        """
        获取全局统计信息（缓存2小时）

        Returns:
            全局统计信息
        """
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        total_projects = db.query(Project).count()
        total_chapters = db.query(Chapter).count()

        total_words = db.query(Chapter).with_entities(Chapter.word_count).all()
        total_word_count = sum(wc[0] or 0 for wc in total_words)

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_projects": total_projects,
            "total_chapters": total_chapters,
            "total_word_count": total_word_count,
        }

    @staticmethod
    def invalidate_global_stats():
        """使全局统计缓存失效"""
        invalidate_pattern("stats:global:*")


# 缓存预热函数
def warmup_cache(db: Session, user_id: Optional[int] = None):
    """
    缓存预热

    Args:
        db: 数据库会话
        user_id: 用户ID（可选，如果提供则只预热该用户的缓存）
    """
    if user_id:
        # 预热特定用户缓存
        UserService.get_user_by_id(db, user_id)
        UserService.get_user_projects(db, user_id)
        UserService.get_user_stats(db, user_id)
    else:
        # 预热全局统计
        StatsService.get_global_stats(db)


# 缓存统计函数
def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    redis = cache_manager.redis

    try:
        info = redis.info("stats")
        keyspace = redis.info("keyspace")

        db_info = keyspace.get("db0", {})
        total_keys = db_info.get("keys", 0) if isinstance(db_info, dict) else 0

        return {
            "total_connections": info.get("total_connections_received", 0),
            "total_commands": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "total_keys": total_keys,
            "hit_rate": (
                info.get("keyspace_hits", 0) /
                (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                * 100
            )
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("缓存服务模块加载成功")
    print("✅ 用户服务: UserService")
    print("✅ 项目服务: ProjectService")
    print("✅ 章节服务: ChapterService")
    print("✅ 统计服务: StatsService")
