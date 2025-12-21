// hooks/useWebSocket.ts
// WebSocket实时通知Hook

import { useEffect, useRef, useCallback } from 'react';
import { message } from 'antd';
import { useAppStore } from '@/store/useAppStore';

export interface WebSocketMessage {
  type: 'task_update' | 'notification' | 'system';
  data: any;
}

export const useWebSocket = (url?: string) => {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const { token, updateTask, addNotification } = useAppStore();

  const connect = useCallback(() => {
    if (!token) {
      console.log('WebSocket: 未登录，跳过连接');
      return;
    }

    // 使用提供的URL或默认URL
    const wsUrl = url || `ws://localhost:8000/ws?token=${token}`;

    try {
      console.log('WebSocket: 尝试连接...', wsUrl);
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket: 已连接');
        reconnectAttempts.current = 0;
        message.success('实时通知已连接');
      };

      ws.current.onmessage = (event) => {
        try {
          const msg: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket: 收到消息', msg);

          switch (msg.type) {
            case 'task_update':
              // 更新任务状态
              if (msg.data.task_id) {
                updateTask(msg.data.task_id, {
                  status: msg.data.status,
                  progress: msg.data.progress,
                  message: msg.data.message,
                  result: msg.data.result,
                });

                // 如果任务完成或失败，显示通知
                if (msg.data.status === 'completed') {
                  addNotification({
                    type: 'success',
                    message: '任务完成',
                    description: msg.data.message,
                  });
                } else if (msg.data.status === 'failed') {
                  addNotification({
                    type: 'error',
                    message: '任务失败',
                    description: msg.data.message,
                  });
                }
              }
              break;

            case 'notification':
              // 显示系统通知
              addNotification({
                type: msg.data.type || 'info',
                message: msg.data.message,
                description: msg.data.description,
              });
              break;

            case 'system':
              // 系统消息
              if (msg.data.action === 'reload') {
                message.info('系统已更新，请刷新页面');
              }
              break;

            default:
              console.warn('WebSocket: 未知消息类型', msg.type);
          }
        } catch (error) {
          console.error('WebSocket: 解析消息失败', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket: 连接错误', error);
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket: 连接已关闭', event.code, event.reason);

        // 自动重连
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`WebSocket: ${delay}ms 后尝试重连...`);

          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current += 1;
            connect();
          }, delay);
        } else {
          console.log('WebSocket: 达到最大重连次数，停止重连');
          message.warning('实时通知连接失败，请刷新页面重试');
        }
      };
    } catch (error) {
      console.error('WebSocket: 创建连接失败', error);
    }
  }, [token, url, updateTask, addNotification]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }

    if (ws.current) {
      console.log('WebSocket: 主动断开连接');
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const send = useCallback((message: WebSocketMessage) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket: 连接未打开，无法发送消息');
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    send,
    disconnect,
    reconnect: connect,
    isConnected: ws.current?.readyState === WebSocket.OPEN,
  };
};
