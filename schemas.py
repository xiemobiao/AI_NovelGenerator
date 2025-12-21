# schemas.py
# -*- coding: utf-8 -*-
"""
Pydantic模型定义
用于API请求验证和响应序列化
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"


class ProjectStatusEnum(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"


class ChapterStatusEnum(str, Enum):
    DRAFT = "draft"
    FINAL = "final"


# ==================== 用户相关 ====================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=6, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str


class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    """用户密码更新模型"""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    avatar: Optional[str]
    role: UserRoleEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 认证相关 ====================

class Token(BaseModel):
    """JWT Token响应"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class AuthResponse(BaseModel):
    """认证响应"""
    user: UserResponse
    token: str


# ==================== 项目相关 ====================

class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., min_length=1, max_length=200)
    genre: str
    topic: Optional[str] = None
    num_chapters: int = Field(..., ge=1, le=500)


class ProjectCreate(ProjectBase):
    """项目创建模型"""
    filepath: str


class ProjectUpdate(BaseModel):
    """项目更新模型"""
    name: Optional[str] = None
    status: Optional[ProjectStatusEnum] = None


class ProjectResponse(ProjectBase):
    """项目响应模型"""
    id: int
    filepath: str
    status: ProjectStatusEnum
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 章节相关 ====================

class ChapterBase(BaseModel):
    """章节基础模型"""
    chapter_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = ""


class ChapterCreate(ChapterBase):
    """章节创建模型"""
    project_id: int


class ChapterUpdate(BaseModel):
    """章节更新模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[ChapterStatusEnum] = None


class ChapterResponse(ChapterBase):
    """章节响应模型"""
    id: int
    word_count: int
    status: ChapterStatusEnum
    project_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 版本历史相关 ====================

class ChapterVersionBase(BaseModel):
    """版本基础模型"""
    content: str
    change_description: Optional[str] = None


class ChapterVersionCreate(ChapterVersionBase):
    """版本创建模型"""
    chapter_id: int


class ChapterVersionResponse(ChapterVersionBase):
    """版本响应模型"""
    id: int
    version_number: int
    word_count: int
    chapter_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 列表响应 ====================

class PaginatedResponse(BaseModel):
    """分页响应基础模型"""
    total: int
    page: int
    page_size: int
    items: List


class ProjectListResponse(PaginatedResponse):
    """项目列表响应"""
    items: List[ProjectResponse]


class ChapterListResponse(PaginatedResponse):
    """章节列表响应"""
    items: List[ChapterResponse]


class VersionListResponse(BaseModel):
    """版本历史列表响应"""
    total: int
    items: List[ChapterVersionResponse]
