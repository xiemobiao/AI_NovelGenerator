# API文档

## 概述

AI Novel Generator API 提供完整的 RESTful API 接口，支持远程调用小说生成功能。

**版本**: 1.5.0
**基础URL**: `http://localhost:8000`
**API文档**: `http://localhost:8000/docs`
**ReDoc文档**: `http://localhost:8000/redoc`

## 快速开始

### 1. 启动API服务器

```bash
# 方式1: 直接运行
python api_server.py

# 方式2: 使用uvicorn（推荐）
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 访问交互式文档

打开浏览器访问: `http://localhost:8000/docs`

## API端点

### 基础端点

#### GET /
获取API基本信息

**响应示例**:
```json
{
  "message": "AI Novel Generator API",
  "version": "1.5.0",
  "docs": "/docs",
  "health": "/health"
}
```

#### GET /health
健康检查

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-03-15T10:30:00",
  "active_tasks": 0
}
```

---

### 生成端点

#### POST /api/v1/novel/architecture
生成小说架构（Step 1）

**请求体**:
```json
{
  "novel_config": {
    "topic": "穿越到异世界的程序员",
    "genre": "玄幻",
    "num_chapters": 100,
    "word_number": 3000,
    "content_guidance": "轻松幽默，带有科技元素",
    "core_characters": "主角：李明，配角：精灵公主",
    "key_items": "笔记本电脑，魔法水晶",
    "scenes": "现代都市，魔法学院",
    "time_constraints": "三个月内完成冒险"
  },
  "llm_config": {
    "interface_format": "OpenAI",
    "api_key": "sk-xxx",
    "base_url": "https://api.openai.com/v1",
    "model_name": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 8192,
    "timeout": 600
  },
  "embedding_config": {
    "interface_format": "OpenAI",
    "api_key": "sk-xxx",
    "base_url": "https://api.openai.com/v1",
    "model_name": "text-embedding-ada-002",
    "retrieval_k": 4
  },
  "output_dir": "./my_novel",
  "project_name": "异世界程序员"
}
```

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "架构生成任务已创建",
  "status_url": "/api/v1/task/550e8400-e29b-41d4-a716-446655440000"
}
```

#### POST /api/v1/novel/blueprint
生成章节目录（Step 2）

**请求体**: 同架构生成

**响应**: 返回任务ID

#### POST /api/v1/novel/chapter
生成章节草稿（Step 3）

**请求体**:
```json
{
  "project_id": "./my_novel",
  "chapter_number": 1,
  "chapter_guidance": "主角初到异世界，遇到精灵公主"
}
```

**响应**: 返回任务ID

#### POST /api/v1/novel/finalize
定稿章节（Step 4）

**请求体**:
```json
{
  "project_id": "./my_novel",
  "chapter_number": 1,
  "chapter_guidance": null
}
```

**响应**: 返回任务ID

---

### 导出端点

#### POST /api/v1/novel/export
导出小说

**支持格式**: `txt`, `epub`, `pdf`, `docx`

**请求体**:
```json
{
  "project_id": "./my_novel",
  "format": "epub",
  "title": "异世界程序员",
  "author": "张三",
  "num_chapters": 10
}
```

**响应示例**:
```json
{
  "message": "导出成功",
  "file": "./my_novel/novel.epub",
  "format": "epub"
}
```

---

### 任务管理端点

#### GET /api/v1/task/{task_id}
查询任务状态

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100.0,
  "message": "架构生成完成",
  "created_at": "2025-03-15T10:30:00",
  "updated_at": "2025-03-15T10:35:00",
  "result": {
    "architecture_file": "./my_novel/Novel_architecture.txt"
  },
  "error": null
}
```

**任务状态**:
- `pending`: 等待中
- `running`: 运行中
- `completed`: 已完成
- `failed`: 失败

#### GET /api/v1/tasks
列出所有任务

**查询参数**:
- `status`: 过滤任务状态（可选）
- `limit`: 返回数量限制（默认50）

**响应示例**:
```json
{
  "total": 10,
  "tasks": [...]
}
```

#### DELETE /api/v1/task/{task_id}
删除任务记录

**注意**: 无法删除正在运行的任务

---

### 项目管理端点

#### GET /api/v1/projects
列出所有项目

**查询参数**:
- `base_dir`: 基础目录（默认当前目录）

**响应示例**:
```json
{
  "total": 3,
  "projects": [
    {
      "id": "./my_novel",
      "name": "my_novel",
      "has_architecture": true,
      "has_directory": true,
      "chapter_count": 5,
      "created_at": "2025-03-15T10:00:00"
    }
  ]
}
```

---

## 使用示例

### Python客户端示例

```python
import requests
import time

API_BASE = "http://localhost:8000"

# 1. 创建架构生成任务
response = requests.post(f"{API_BASE}/api/v1/novel/architecture", json={
    "novel_config": {
        "topic": "太空探险",
        "genre": "科幻",
        "num_chapters": 50,
        "word_number": 3000
    },
    "llm_config": {
        "interface_format": "OpenAI",
        "api_key": "your-api-key",
        "model_name": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 8192
    },
    "embedding_config": {
        "interface_format": "OpenAI",
        "api_key": "your-api-key",
        "model_name": "text-embedding-ada-002"
    },
    "output_dir": "./space_novel"
})

task_id = response.json()["task_id"]
print(f"任务ID: {task_id}")

# 2. 轮询任务状态
while True:
    response = requests.get(f"{API_BASE}/api/v1/task/{task_id}")
    task = response.json()

    print(f"状态: {task['status']}, 进度: {task['progress']}%")

    if task['status'] in ['completed', 'failed']:
        break

    time.sleep(5)

# 3. 导出小说
if task['status'] == 'completed':
    response = requests.post(f"{API_BASE}/api/v1/novel/export", json={
        "project_id": "./space_novel",
        "format": "epub",
        "title": "太空探险记",
        "author": "AI作者"
    })
    print(f"导出结果: {response.json()}")
```

### cURL示例

```bash
# 健康检查
curl http://localhost:8000/health

# 列出项目
curl http://localhost:8000/api/v1/projects

# 导出小说
curl -X POST http://localhost:8000/api/v1/novel/export \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "./my_novel",
    "format": "txt",
    "title": "我的小说"
  }'
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| 状态码 | 说明 |
|-------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 性能优化建议

1. **并发控制**: API使用后台任务处理长时间操作，建议控制并发任务数量
2. **轮询间隔**: 查询任务状态时建议5-10秒的轮询间隔
3. **超时设置**: 大型项目生成可能需要较长时间，建议设置合理的超时时间
4. **资源管理**: 定期清理已完成的任务记录

---

## 安全建议

⚠️ **生产环境部署注意事项**:

1. **API密钥保护**: 不要在客户端暴露API密钥
2. **CORS配置**: 限制允许的源域名
3. **认证授权**: 添加身份验证机制
4. **HTTPS**: 使用SSL/TLS加密传输
5. **速率限制**: 实施API调用速率限制

---

## 更多信息

- [开发文档](./DEVELOPMENT.md)
- [使用教程](./TUTORIAL.md)
- [FAQ](../README.md#疑难解答)
