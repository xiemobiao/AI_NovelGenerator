# websocket_manager.py
# -*- coding: utf-8 -*-
"""
WebSocket连接管理器
管理WebSocket连接、消息广播和用户通知
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 存储活跃连接: {user_id: Set[WebSocket]}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # 存储连接元数据: {websocket_id: user_id}
        self.connection_metadata: Dict[int, int] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        建立WebSocket连接

        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
        """
        await websocket.accept()

        # 添加到活跃连接
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_metadata[id(websocket)] = user_id

        logger.info(f"WebSocket连接建立: user_id={user_id}, 当前连接数={len(self.active_connections[user_id])}")

        # 发送欢迎消息
        await self.send_personal_message(
            user_id=user_id,
            message={
                "type": "system",
                "data": {
                    "message": "WebSocket连接成功",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    def disconnect(self, websocket: WebSocket):
        """
        断开WebSocket连接

        Args:
            websocket: WebSocket连接对象
        """
        ws_id = id(websocket)
        user_id = self.connection_metadata.get(ws_id)

        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # 如果用户没有其他连接，移除该用户
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

            # 移除元数据
            if ws_id in self.connection_metadata:
                del self.connection_metadata[ws_id]

            logger.info(f"WebSocket连接断开: user_id={user_id}")

    async def send_personal_message(self, user_id: int, message: dict):
        """
        发送消息给指定用户的所有连接

        Args:
            user_id: 用户ID
            message: 消息字典
        """
        if user_id in self.active_connections:
            # 发送给该用户的所有活跃连接
            dead_connections = []

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    dead_connections.append(connection)

            # 清理失效连接
            for connection in dead_connections:
                self.disconnect(connection)

    async def broadcast_to_all(self, message: dict):
        """
        广播消息给所有用户

        Args:
            message: 消息字典
        """
        dead_connections = []

        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"广播消息失败: {e}")
                    dead_connections.append(connection)

        # 清理失效连接
        for connection in dead_connections:
            self.disconnect(connection)

    async def send_task_update(
        self,
        user_id: int,
        task_id: str,
        status: str,
        progress: int,
        message: str,
        result: dict = None
    ):
        """
        发送任务更新通知

        Args:
            user_id: 用户ID
            task_id: 任务ID
            status: 任务状态 (pending/running/completed/failed)
            progress: 进度百分比 (0-100)
            message: 状态消息
            result: 任务结果（可选）
        """
        await self.send_personal_message(
            user_id=user_id,
            message={
                "type": "task_update",
                "data": {
                    "task_id": task_id,
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    async def send_notification(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        description: str = None
    ):
        """
        发送通知消息

        Args:
            user_id: 用户ID
            notification_type: 通知类型 (success/error/info/warning)
            message: 通知标题
            description: 通知详情（可选）
        """
        await self.send_personal_message(
            user_id=user_id,
            message={
                "type": "notification",
                "data": {
                    "type": notification_type,
                    "message": message,
                    "description": description,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    async def send_chapter_saved_notification(
        self,
        user_id: int,
        chapter_number: int,
        chapter_title: str,
        word_count: int
    ):
        """
        发送章节保存通知

        Args:
            user_id: 用户ID
            chapter_number: 章节号
            chapter_title: 章节标题
            word_count: 字数
        """
        await self.send_notification(
            user_id=user_id,
            notification_type="success",
            message=f"第{chapter_number}章已保存",
            description=f"{chapter_title} - {word_count}字"
        )

    def get_active_users(self) -> List[int]:
        """
        获取所有在线用户ID列表

        Returns:
            在线用户ID列表
        """
        return list(self.active_connections.keys())

    def get_user_connection_count(self, user_id: int) -> int:
        """
        获取指定用户的连接数

        Args:
            user_id: 用户ID

        Returns:
            连接数
        """
        return len(self.active_connections.get(user_id, []))

    def is_user_online(self, user_id: int) -> bool:
        """
        检查用户是否在线

        Args:
            user_id: 用户ID

        Returns:
            是否在线
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# 全局连接管理器实例
manager = ConnectionManager()
