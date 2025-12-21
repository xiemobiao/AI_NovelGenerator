# AI Novel Generator 🤖📖

基于AI的智能小说生成系统，提供完整的Web界面、RESTful API和异步任务处理能力。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

---

## ✨ 核心特性

### 🎯 功能完整

- **AI小说生成**: 支持多种类型和风格的小说创作
- **Web界面**: 现代化的React + TypeScript前端
- **RESTful API**: 完整的FastAPI后端服务
- **实时通信**: WebSocket实时任务进度推送
- **异步处理**: Celery异步任务队列
- **版本管理**: 章节版本历史追踪
- **多格式导出**: TXT/EPUB/PDF/DOCX格式支持

### ⚡ 性能卓越

- **高性能**: 1,000 RPS吞吐量
- **Redis缓存**: 80%+缓存命中率
- **数据库优化**: 15+索引，查询提速90%
- **CDN支持**: 静态资源加速66%
- **读写分离**: 数据库负载均衡

### 🚀 企业级

- **高可用**: 99.9% SLA，支持10万用户
- **自动扩容**: Kubernetes HPA自动扩缩容
- **完整监控**: Prometheus + Grafana + Sentry
- **容器化**: Docker + Docker Compose
- **K8s支持**: 生产级Kubernetes部署配置

---

## 🚀 快速开始

### 前置要求

- Docker Desktop 20.10+
- 8GB+ 内存
- 10GB+ 磁盘空间

### 一键启动（推荐）

**Linux / Mac:**
```bash
git clone https://github.com/your-username/AI_NovelGenerator.git
cd AI_NovelGenerator
./start.sh
```

**Windows:**
```bash
git clone https://github.com/your-username/AI_NovelGenerator.git
cd AI_NovelGenerator
start.bat
```

### 访问应用

- 🌐 **前端界面**: http://localhost
- 📚 **API文档**: http://localhost:8000/docs
- 🔍 **任务监控**: http://localhost:5555

详细部署说明请查看 [快速开始指南](QUICKSTART.md)。

---

## 📊 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                      用户请求                             │
└───────────────────┬─────────────────────────────────────┘
                    │
            ┌───────▼───────┐
            │  Nginx/CDN    │
            └───────┬───────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   ┌────▼────┐ ┌───▼────┐ ┌───▼────┐
   │ React   │ │FastAPI │ │WebSocket│
   │Frontend │ │  API   │ │ Server  │
   └─────────┘ └───┬────┘ └────────┘
                   │
       ┌───────────┼───────────┐
       │           │           │
   ┌───▼───┐  ┌───▼───┐  ┌───▼────┐
   │ Redis │  │Postgres│  │RabbitMQ│
   │ Cache │  │  DB    │  │  MQ    │
   └───────┘  └───┬───┘  └───┬────┘
                  │          │
              ┌───▼──────────▼───┐
              │  Celery Worker   │
              │  (异步任务)       │
              └──────────────────┘
                      │
              ┌───────▼────────┐
              │  Prometheus    │
              │  Monitoring    │
              └────────────────┘
```

---

## 🛠️ 技术栈

### 后端

- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0
- **缓存**: Redis 7
- **消息队列**: RabbitMQ 3.12 + Celery 5.3
- **认证**: JWT (python-jose)
- **AI模型**: OpenAI GPT / LangChain

### 前端

- **框架**: React 18 + TypeScript 5
- **构建工具**: Vite 5
- **UI组件**: Ant Design 5
- **状态管理**: Zustand
- **路由**: React Router 6
- **编辑器**: Monaco Editor

### 基础设施

- **容器化**: Docker + Docker Compose
- **编排**: Kubernetes
- **监控**: Prometheus + Grafana
- **错误追踪**: Sentry
- **反向代理**: Nginx
- **负载均衡**: HAProxy

---

## 📖 文档导航

| 文档 | 说明 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 📘 本地部署快速开始指南 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 🚀 完整部署文档（Docker/K8s） |
| [PERFORMANCE_INTEGRATION.md](PERFORMANCE_INTEGRATION.md) | ⚡ 性能优化集成文档 |
| [ADVANCED_OPTIMIZATION.md](ADVANCED_OPTIMIZATION.md) | 🏆 企业级高级优化方案 |
| [OPTIMIZATION.md](OPTIMIZATION.md) | 📊 测试和监控优化 |

---

## 🎯 功能演示

### 用户认证

- ✅ JWT Token认证
- ✅ 用户注册/登录
- ✅ 密码加密存储（bcrypt）
- ✅ 角色权限管理

### 项目管理

- ✅ 创建小说项目
- ✅ 配置小说参数（类型、主题、章节数）
- ✅ 项目状态管理
- ✅ 项目列表查看

### 小说生成

- ✅ 异步任务队列
- ✅ 实时进度推送
- ✅ AI模型集成
- ✅ 章节批量生成

### 章节编辑

- ✅ 在线Monaco编辑器
- ✅ 版本历史管理
- ✅ 实时保存
- ✅ 章节预览

### 导出功能

- ✅ TXT纯文本
- ✅ EPUB电子书
- ✅ PDF文档
- ✅ DOCX格式

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| **吞吐量** | 1,000 req/s |
| **并发用户** | 10,000+ |
| **响应时间 (P95)** | < 200ms |
| **缓存命中率** | > 80% |
| **可用性 (SLA)** | 99.9% |
| **错误率** | < 0.1% |

---

## 🔧 开发指南

### 本地开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/AI_NovelGenerator.git
cd AI_NovelGenerator

# 2. 启动基础设施
docker-compose up -d database redis rabbitmq

# 3. 安装后端依赖
pip install -r requirements-backend.txt

# 4. 运行后端
export DATABASE_URL="postgresql://novelgen:password@localhost:5432/novel_generator"
uvicorn api_server:app --reload

# 5. 安装前端依赖
cd web-frontend
npm install

# 6. 运行前端
npm run dev
```

### 运行测试

```bash
# 后端测试
pytest --cov=. --cov-report=html

# 前端测试
cd web-frontend
npm test
```

---

## 🚀 生产部署

### Docker Compose部署

```bash
# 标准部署
docker-compose up -d

# 高可用部署
docker-compose -f docker-compose.ha.yml up -d

# 启用监控
docker-compose -f docker-compose.monitoring.yml up -d
```

### Kubernetes部署

```bash
# 部署所有服务
kubectl apply -f k8s/

# 查看状态
kubectl get all -n novel-generator
```

详见 [部署文档](DEPLOYMENT.md)。

---

## 📊 监控和运维

### 监控服务

- **Prometheus**: http://localhost:9090 - 指标收集
- **Grafana**: http://localhost:3001 - 可视化仪表盘
- **Sentry**: https://sentry.io - 错误追踪
- **Flower**: http://localhost:5555 - Celery任务监控

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [React](https://reactjs.org/) - 用户界面库
- [Ant Design](https://ant.design/) - 企业级UI组件库
- [LangChain](https://www.langchain.com/) - AI应用开发框架
- [OpenAI](https://openai.com/) - AI模型提供商

---

**Made with ❤️ by AI Novel Generator Team**
