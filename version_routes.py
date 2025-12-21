# version_routes.py
# -*- coding: utf-8 -*-
"""
章节版本历史相关的API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, Chapter, ChapterVersion
from schemas import ChapterVersionResponse, VersionListResponse
from auth import get_current_user

router = APIRouter(prefix="/chapters", tags=["版本历史"])


# ==================== 获取章节版本列表 ====================

@router.get("/{chapter_id}/versions", response_model=VersionListResponse)
async def get_chapter_versions(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定章节的所有版本历史

    - **chapter_id**: 章节ID

    返回版本列表，按创建时间倒序排列（最新的在前）
    需要认证
    """
    # 检查章节是否存在
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )

    # 检查章节是否属于当前用户的项目
    if chapter.project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此章节"
        )

    # 获取所有版本
    versions = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id
    ).order_by(ChapterVersion.created_at.desc()).all()

    return VersionListResponse(
        total=len(versions),
        items=[ChapterVersionResponse.from_orm(v) for v in versions]
    )


# ==================== 获取指定版本详情 ====================

@router.get("/{chapter_id}/versions/{version_id}", response_model=ChapterVersionResponse)
async def get_chapter_version(
    chapter_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取章节的指定版本详情

    - **chapter_id**: 章节ID
    - **version_id**: 版本ID

    返回版本详细信息
    需要认证
    """
    # 检查章节是否存在
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )

    # 检查章节是否属于当前用户
    if chapter.project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此章节"
        )

    # 获取指定版本
    version = db.query(ChapterVersion).filter(
        ChapterVersion.id == version_id,
        ChapterVersion.chapter_id == chapter_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版本不存在"
        )

    return ChapterVersionResponse.from_orm(version)


# ==================== 创建新版本（保存章节时自动调用） ====================

def create_chapter_version(
    db: Session,
    chapter_id: int,
    user_id: int,
    content: str,
    change_description: str = None
) -> ChapterVersion:
    """
    创建章节新版本

    这是内部函数，在保存章节时自动调用

    Args:
        db: 数据库会话
        chapter_id: 章节ID
        user_id: 创建者ID
        content: 章节内容
        change_description: 修改说明

    Returns:
        新创建的ChapterVersion对象
    """
    # 获取当前版本号
    latest_version = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id
    ).order_by(ChapterVersion.version_number.desc()).first()

    next_version_number = 1
    if latest_version:
        next_version_number = latest_version.version_number + 1

    # 创建新版本
    new_version = ChapterVersion(
        chapter_id=chapter_id,
        version_number=next_version_number,
        content=content,
        word_count=len(content),
        change_description=change_description,
        created_by=user_id
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return new_version


# ==================== 恢复到指定版本 ====================

@router.post("/{chapter_id}/versions/{version_id}/restore", status_code=status.HTTP_200_OK)
async def restore_chapter_version(
    chapter_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    恢复章节到指定版本

    - **chapter_id**: 章节ID
    - **version_id**: 要恢复的版本ID

    将章节内容恢复到指定版本，并创建一个新版本记录
    需要认证
    """
    # 检查章节是否存在
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )

    # 检查权限
    if chapter.project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此章节"
        )

    # 获取要恢复的版本
    version = db.query(ChapterVersion).filter(
        ChapterVersion.id == version_id,
        ChapterVersion.chapter_id == chapter_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版本不存在"
        )

    # 保存当前内容为新版本（恢复前）
    create_chapter_version(
        db=db,
        chapter_id=chapter_id,
        user_id=current_user.id,
        content=chapter.content,
        change_description=f"恢复前的版本（准备恢复到版本{version.version_number}）"
    )

    # 恢复章节内容
    chapter.content = version.content
    chapter.word_count = version.word_count

    # 创建恢复后的新版本
    restored_version = create_chapter_version(
        db=db,
        chapter_id=chapter_id,
        user_id=current_user.id,
        content=version.content,
        change_description=f"从版本{version.version_number}恢复"
    )

    db.commit()

    return {
        "message": "版本恢复成功",
        "restored_to_version": version.version_number,
        "new_version_number": restored_version.version_number
    }


# ==================== 删除版本（可选功能，谨慎使用） ====================

@router.delete("/{chapter_id}/versions/{version_id}", status_code=status.HTTP_200_OK)
async def delete_chapter_version(
    chapter_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除指定版本

    ⚠️ 警告: 此操作不可恢复！

    - **chapter_id**: 章节ID
    - **version_id**: 版本ID

    需要认证且只能删除自己创建的版本
    """
    # 检查章节是否存在
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )

    # 检查权限
    if chapter.project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此章节"
        )

    # 获取要删除的版本
    version = db.query(ChapterVersion).filter(
        ChapterVersion.id == version_id,
        ChapterVersion.chapter_id == chapter_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版本不存在"
        )

    # 检查版本总数，至少保留一个版本
    version_count = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id
    ).count()

    if version_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除唯一的版本，至少需要保留一个版本"
        )

    # 删除版本
    db.delete(version)
    db.commit()

    return {"message": "版本已删除"}
