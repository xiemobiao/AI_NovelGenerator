# 快速开始 - 本地部署指南

本指南帮助您在本地快速部署并体验AI Novel Generator的完整功能。

---

## 📋 前置要求

### 必需软件

- **Docker Desktop** (>= 20.10)
  - [Mac下载](https://www.docker.com/products/docker-desktop)
  - [Windows下载](https://www.docker.com/products/docker-desktop)
  - [Linux安装](https://docs.docker.com/engine/install/)

- **Docker Compose** (>= 2.0)
  - Docker Desktop已包含
  - Linux需单独安装: `sudo apt install docker-compose-plugin`

### 可选软件（用于开发）

- Python 3.11+
- Node.js 18+
- Git

### 系统要求

- **内存**: 最少8GB，推荐16GB
- **磁盘**: 最少10GB可用空间
- **CPU**: 2核心以上

---

## 🚀 方式一：一键启动（推荐）

### 1. 克隆项目（如果还没有）

```bash
git clone https://github.com/your-username/AI_NovelGenerator.git
cd AI_NovelGenerator
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，至少需要配置以下内容：
# OPENAI_API_KEY=your-openai-api-key-here
# SECRET_KEY=your-secret-key-for-jwt
# DB_PASSWORD=your-database-password
```

### 3. 启动所有服务

```bash
# 启动基础服务（数据库、Redis、RabbitMQ、后端、前端）
docker-compose up -d

# 查看启动日志
docker-compose logs -f

# 等待所有服务启动完成（约1-2分钟）
```

### 4. 访问应用

启动完成后，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端界面** | http://localhost | 主要的Web界面 |
| **API文档** | http://localhost:8000/docs | Swagger API文档 |
| **API接口** | http://localhost:8000 | 后端API |
| **Flower监控** | http://localhost:5555 | Celery任务监控 |
| **RabbitMQ管理** | http://localhost:15672 | 消息队列管理 (admin/admin_password) |

### 5. 验证部署

```bash
# 检查所有容器是否正常运行
docker-compose ps

# 应该看到以下容器都是 "running" 状态：
# - novel-generator-db
# - novel-generator-redis
# - novel-generator-rabbitmq
# - novel-generator-backend
# - novel-generator-celery-worker
# - novel-generator-celery-beat
# - novel-generator-flower
# - novel-generator-frontend
```

### 6. 创建第一个用户

访问 http://localhost 进行注册：

```
用户名: admin
邮箱: admin@example.com
密码: Admin123456
```

### 7. 测试小说生成

1. 登录后点击"新建项目"
2. 填写项目信息：
   - 项目名称: 我的第一部小说
   - 类型: 科幻
   - 主题: AI觉醒
   - 章节数: 5
3. 点击"开始生成"
4. 在"任务监控"页面查看生成进度

---

## 🔍 方式二：分步启动（调试模式）

如果需要调试或逐步了解各个组件，可以按以下步骤操作：

### 1. 只启动基础设施

```bash
# 只启动数据库、Redis、RabbitMQ
docker-compose up -d database redis rabbitmq

# 等待服务就绪
docker-compose logs -f database redis rabbitmq
```

### 2. 启动后端API

```bash
# 选项A：使用Docker
docker-compose up -d backend

# 选项B：本地运行（需要Python 3.11+）
pip install -r requirements-backend.txt
export DATABASE_URL="postgresql://novelgen:change_this_password@localhost:5432/novel_generator"
export REDIS_HOST="localhost"
export REDIS_PASSWORD="redis_password"
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动Celery Worker

```bash
# 选项A：使用Docker
docker-compose up -d celery-worker celery-beat flower

# 选项B：本地运行
celery -A celery_app worker --loglevel=info --concurrency=4
celery -A celery_app beat --loglevel=info
celery -A celery_app flower --port=5555
```

### 4. 启动前端

```bash
# 选项A：使用Docker
docker-compose up -d frontend

# 选项B：本地运行（需要Node.js 18+）
cd web-frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

---

## 🐛 故障排查

### 问题1：端口被占用

```bash
# 错误信息：Bind for 0.0.0.0:8000 failed: port is already allocated

# 解决方法1：停止占用端口的服务
# Mac/Linux
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# 解决方法2：修改docker-compose.yml中的端口映射
# ports:
#   - "8001:8000"  # 改用8001端口
```

### 问题2：容器启动失败

```bash
# 查看错误日志
docker-compose logs backend

# 常见原因：
# 1. 环境变量未配置
# 2. 数据库未就绪

# 解决方法：
# 1. 检查.env文件
cat .env

# 2. 重启服务
docker-compose restart backend

# 3. 重新构建
docker-compose up -d --build backend
```

### 问题3：数据库连接失败

```bash
# 检查数据库是否运行
docker-compose ps database

# 进入数据库容器检查
docker-compose exec database psql -U novelgen -d novel_generator -c "SELECT 1;"

# 如果失败，重新初始化
docker-compose down -v  # 警告：会删除所有数据
docker-compose up -d database
```

### 问题4：Redis连接失败

```bash
# 测试Redis连接
docker-compose exec redis redis-cli -a redis_password ping
# 应该返回 PONG

# 如果失败，检查密码配置
grep REDIS_PASSWORD .env
```

### 问题5：前端无法访问后端API

```bash
# 检查CORS配置
# 在 api_server.py 中应该有：
# allow_origins=["*"]  # 开发环境
# 或
# allow_origins=["http://localhost", "http://localhost:3000"]

# 临时解决：允许所有来源
# 在 .env 中添加：
CORS_ORIGINS=*
```

---

## 🔧 常用命令

### Docker相关

```bash
# 查看所有容器状态
docker-compose ps

# 查看日志
docker-compose logs -f backend          # 后端日志
docker-compose logs -f celery-worker    # Worker日志
docker-compose logs -f --tail=100 backend  # 最近100行

# 重启服务
docker-compose restart backend
docker-compose restart celery-worker

# 停止所有服务
docker-compose stop

# 停止并删除所有容器
docker-compose down

# 停止并删除所有数据（包括数据卷）
docker-compose down -v  # ⚠️ 警告：会删除所有数据

# 重新构建镜像
docker-compose build backend
docker-compose up -d --build backend

# 进入容器
docker-compose exec backend bash
docker-compose exec database psql -U novelgen -d novel_generator
docker-compose exec redis redis-cli -a redis_password
```

### 数据库相关

```bash
# 进入数据库
docker-compose exec database psql -U novelgen -d novel_generator

# 查看所有表
\dt

# 查看用户数据
SELECT * FROM users;

# 查看项目数据
SELECT * FROM projects;

# 退出
\q

# 备份数据库
docker-compose exec database pg_dump -U novelgen novel_generator > backup.sql

# 恢复数据库
docker-compose exec -T database psql -U novelgen novel_generator < backup.sql
```

### Celery相关

```bash
# 查看活跃任务
docker-compose exec celery-worker celery -A celery_app inspect active

# 查看已注册任务
docker-compose exec celery-worker celery -A celery_app inspect registered

# 查看Worker状态
docker-compose exec celery-worker celery -A celery_app inspect stats

# 清空所有队列
docker-compose exec celery-worker celery -A celery_app purge
```

---

## 📊 启动监控栈（可选）

如果想体验完整的监控功能：

```bash
# 启动Prometheus + Grafana
docker-compose -f docker-compose.monitoring.yml up -d

# 访问监控服务
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3001 (admin/admin)
# Node Exporter: http://localhost:9100/metrics
# cAdvisor:   http://localhost:8080
```

### Grafana配置

1. 访问 http://localhost:3001
2. 登录：admin / admin（首次登录需修改密码）
3. 添加数据源：
   - 类型：Prometheus
   - URL: http://prometheus:9090
   - 点击"Save & Test"
4. 导入仪表盘：
   - 点击 "+" → "Import"
   - Dashboard ID: 1860（Node Exporter）
   - Dashboard ID: 11074（FastAPI）

---

## 🎯 测试功能清单

启动完成后，建议按以下顺序测试功能：

### 1. 用户认证 ✅

- [ ] 注册新用户
- [ ] 登录
- [ ] 查看个人信息
- [ ] 修改密码

### 2. 项目管理 ✅

- [ ] 创建新项目
- [ ] 查看项目列表
- [ ] 编辑项目信息
- [ ] 删除项目

### 3. 小说生成 ✅

- [ ] 配置小说参数（主题、类型、章节数）
- [ ] 提交生成任务
- [ ] 在Flower监控任务进度
- [ ] 查看生成结果

### 4. 章节管理 ✅

- [ ] 查看章节列表
- [ ] 编辑章节内容
- [ ] 保存版本历史
- [ ] 查看历史版本

### 5. 导出功能 ✅

- [ ] 导出为TXT
- [ ] 导出为EPUB
- [ ] 导出为PDF
- [ ] 导出为DOCX

### 6. 监控功能 ✅

- [ ] 查看API文档 (http://localhost:8000/docs)
- [ ] 查看Celery任务 (http://localhost:5555)
- [ ] 查看Prometheus指标 (http://localhost:9090)
- [ ] 查看Grafana仪表盘 (http://localhost:3001)

---

## 🔐 安全提示（生产环境）

⚠️ **本地部署使用默认密码，仅用于测试。生产环境必须修改以下配置：**

```bash
# .env 文件中修改：
DB_PASSWORD=<强密码>
SECRET_KEY=<随机字符串，至少32字符>
REDIS_PASSWORD=<强密码>
RABBITMQ_PASSWORD=<强密码>
SENTRY_DSN=<你的Sentry DSN>
OPENAI_API_KEY=<你的OpenAI Key>
```

生成安全密钥：

```bash
# 生成32字符随机密钥
openssl rand -hex 32

# 或使用Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📚 下一步

本地部署成功后，您可以：

1. **阅读文档**：
   - `DEPLOYMENT.md` - 完整部署文档
   - `PERFORMANCE_INTEGRATION.md` - 性能优化文档
   - `ADVANCED_OPTIMIZATION.md` - 高级优化文档

2. **体验功能**：
   - 创建项目并生成小说
   - 查看监控数据
   - 测试API接口

3. **开发调试**：
   - 修改代码并实时查看效果
   - 使用API文档测试接口
   - 查看日志排查问题

4. **性能测试**：
   - 使用Locust进行压力测试
   - 查看Prometheus监控指标
   - 优化缓存策略

5. **生产部署**：
   - 配置真实域名和SSL证书
   - 部署到Kubernetes集群
   - 配置CDN和备份策略

---

## 💡 提示

- **首次启动较慢**：Docker需要下载镜像（约1-2GB），请耐心等待
- **数据持久化**：数据存储在Docker卷中，`docker-compose down`不会删除数据
- **清理数据**：使用`docker-compose down -v`删除所有数据（包括数据库）
- **端口冲突**：如果端口被占用，修改`docker-compose.yml`中的端口映射
- **资源占用**：完整部署约占用4GB内存，可根据需要关闭部分服务

---

## 🆘 获取帮助

如果遇到问题：

1. 查看本文档的"故障排查"章节
2. 查看容器日志：`docker-compose logs -f`
3. 访问项目文档目录查看详细文档
4. 提交Issue到GitHub仓库

---

## 🎉 享受使用！

现在您已经在本地成功部署了AI Novel Generator！

开始创作您的第一部AI生成小说吧！🚀📖

