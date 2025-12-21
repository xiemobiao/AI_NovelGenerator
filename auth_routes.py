# auth_routes.py
# -*- coding: utf-8 -*-
"""
认证相关的API路由
包括用户注册、登录、登出等
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
from models import User
from schemas import (
    UserCreate, UserLogin, UserResponse, AuthResponse,
    Token, UserPasswordUpdate, UserUpdate
)
from auth import (
    hash_password, authenticate_user, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["认证"])


# ==================== 用户注册 ====================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名（3-50字符，唯一）
    - **email**: 邮箱地址（唯一）
    - **password**: 密码（至少6个字符）

    返回用户信息和访问令牌
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册"
        )

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建新用户
    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 生成JWT令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id, "username": new_user.username},
        expires_delta=access_token_expires
    )

    return AuthResponse(
        user=UserResponse.from_orm(new_user),
        token=access_token
    )


# ==================== 用户登录 ====================

@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    返回用户信息和访问令牌
    """
    user = authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成JWT令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )

    return AuthResponse(
        user=UserResponse.from_orm(user),
        token=access_token
    )


# ==================== 获取当前用户信息 ====================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息

    需要认证
    """
    return UserResponse.from_orm(current_user)


# ==================== 更新用户信息 ====================

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户信息

    - **email**: 新邮箱（可选）
    - **avatar**: 头像URL（可选）

    需要认证
    """
    # 如果更新邮箱，检查是否已被其他用户使用
    if user_update.email:
        existing = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
        current_user.email = user_update.email

    if user_update.avatar is not None:
        current_user.avatar = user_update.avatar

    db.commit()
    db.refresh(current_user)

    return UserResponse.from_orm(current_user)


# ==================== 修改密码 ====================

@router.post("/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码

    - **old_password**: 旧密码
    - **new_password**: 新密码（至少6个字符）

    需要认证
    """
    from auth import verify_password

    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 更新密码
    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()

    return {"message": "密码修改成功"}


# ==================== 登出 ====================

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出

    注意: JWT是无状态的，实际的登出逻辑在前端完成（删除token）
    此端点主要用于日志记录和可能的token黑名单管理

    需要认证
    """
    # 在实际生产环境中，可以在这里：
    # 1. 记录登出日志
    # 2. 将token加入黑名单（需要Redis等缓存支持）
    # 3. 发送登出通知

    return {"message": "登出成功"}
