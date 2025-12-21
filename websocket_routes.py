# websocket_routes.py
# -*- coding: utf-8 -*-
"""
WebSocket路由
处理WebSocket连接和实时通信
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from database import get_db
from models import User
from auth import decode_access_token
from websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


async def get_user_from_token(token: str, db: Session) -> User:
    """
    从JWT令牌获取用户

    Args:
        token: JWT令牌
        db: 数据库会话

    Returns:
        User对象

    Raises:
        HTTPException: 认证失败
    """
    token_data = decode_access_token(token)

    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )

    return user


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
    db: Session = Depends(get_db)
):
    """
    WebSocket端点

    连接URL示例: ws://localhost:8000/ws?token=YOUR_JWT_TOKEN

    消息格式:
    ```json
    {
        "type": "task_update" | "notification" | "system",
        "data": {
            // 根据type不同而不同
        }
    }
    ```

    需要JWT认证
    """
    try:
        # 验证令牌并获取用户
        user = await get_user_from_token(token, db)

        # 建立连接
        await manager.connect(websocket, user.id)

        try:
            # 保持连接，接收客户端消息
            while True:
                # 接收客户端消息
                data = await websocket.receive_json()

                # 处理客户端消息（可选）
                # 目前主要是服务端主动推送，客户端很少需要发送消息
                # 如果需要处理客户端消息，可以在这里添加逻辑

                logger.info(f"收到来自用户{user.id}的WebSocket消息: {data}")

                # 示例：回显消息
                await manager.send_personal_message(
                    user_id=user.id,
                    message={
                        "type": "echo",
                        "data": {
                            "message": "服务器收到你的消息",
                            "original": data
                        }
                    }
                )

        except WebSocketDisconnect:
            # 客户端主动断开连接
            manager.disconnect(websocket)
            logger.info(f"用户{user.id}的WebSocket连接已断开")

        except Exception as e:
            # 其他错误
            logger.error(f"WebSocket错误: {e}")
            manager.disconnect(websocket)

    except HTTPException as e:
        # 认证失败，拒绝连接
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        logger.warning(f"WebSocket认证失败: {e.detail}")

    except Exception as e:
        # 未知错误
        logger.error(f"WebSocket连接错误: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
