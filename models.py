# models.py
# -*- coding: utf-8 -*-
"""
SQLAlchemy数据库模型定义
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


# ==================== 枚举类型 ====================

class UserRole(str, enum.Enum):
    """用户角色"""
    USER = "user"
    ADMIN = "admin"


class ProjectStatus(str, enum.Enum):
    """项目状态"""
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"


class ChapterStatus(str, enum.Enum):
    """章节状态"""
    DRAFT = "draft"
    FINAL = "final"


# ==================== 数据库模型 ====================

class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    chapter_versions = relationship("ChapterVersion", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    filepath = Column(String(500), nullable=False)
    genre = Column(String(50), nullable=False)
    topic = Column(Text, nullable=True)
    num_chapters = Column(Integer, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)

    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    owner = relationship("User", back_populates="projects")
    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class Chapter(Base):
    """章节模型"""
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False, default="")
    word_count = Column(Integer, default=0, nullable=False)
    status = Column(Enum(ChapterStatus), default=ChapterStatus.DRAFT, nullable=False)

    # 项目关联
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project", back_populates="chapters")
    versions = relationship("ChapterVersion", back_populates="chapter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter(id={self.id}, number={self.chapter_number}, title='{self.title}')>"


class ChapterVersion(Base):
    """章节版本历史模型"""
    __tablename__ = "chapter_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_number = Column(Integer, nullable=False)  # 版本号（1, 2, 3...）
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    change_description = Column(Text, nullable=True)  # 修改说明

    # 章节关联
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)

    # 创建者关联
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    chapter = relationship("Chapter", back_populates="versions")
    creator = relationship("User", back_populates="chapter_versions")

    def __repr__(self):
        return f"<ChapterVersion(id={self.id}, chapter_id={self.chapter_id}, version={self.version_number})>"
