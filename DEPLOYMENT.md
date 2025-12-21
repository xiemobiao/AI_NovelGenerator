# AI Novel Generator 部署文档

完整的生产环境部署指南

---

## 📋 目录

1. [系统要求](#系统要求)
2. [快速开始](#快速开始)
3. [详细部署步骤](#详细部署步骤)
4. [配置说明](#配置说明)
5. [常见问题](#常见问题)
6. [监控和维护](#监控和维护)

---

## 🖥️ 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB SSD
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+) / macOS / Windows with WSL2

### 推荐配置
- **CPU**: 4核心+
- **内存**: 8GB+ RAM
- **存储**: 50GB+ SSD
- **操作系统**: Ubuntu 22.04 LTS

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.0+

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/AI_NovelGenerator.git
cd AI_NovelGenerator
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（必须修改SECRET_KEY和数据库密码！）
nano .env
```

**必须修改的关键配置**:
- `SECRET_KEY`: 使用随机字符串（可以用 `openssl rand -hex 32` 生成）
- `DB_PASSWORD`: 数据库密码
- `OPENAI_API_KEY`: 你的OpenAI API密钥

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问应用

- **Web界面**: http://localhost
- **API文档**: http://localhost:8000/docs
- **数据库**: localhost:5432

### 5. 创建管理员账户

首次部署后，访问Web界面注册第一个用户（默认为普通用户）。

---

## 📝 详细部署步骤

### 步骤1: 准备服务器

#### Ubuntu/Debian

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo apt install docker-compose-plugin -y

# 将当前用户添加到docker组
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker compose version
```

#### CentOS/RHEL

```bash
# 安装Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

### 步骤2: 配置防火墙

```bash
# Ubuntu (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### 步骤3: 配置HTTPS（可选但推荐）

使用Let's Encrypt免费SSL证书:

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书（将example.com替换为你的域名）
sudo certbot --nginx -d example.com -d www.example.com

# 自动续期
sudo certbot renew --dry-run
```

修改 `docker-compose.yml` 添加SSL支持:

```yaml
frontend:
  ports:
    - "80:80"
    - "443:443"  # 添加HTTPS端口
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro  # 挂载SSL证书
```

### 步骤4: 数据备份策略

#### 自动备份脚本

```bash
#!/bin/bash
# backup.sh - 数据库备份脚本

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
docker exec novel-generator-db pg_dump -U novelgen novel_generator > $BACKUP_DIR/db_backup_$DATE.sql

# 压缩
gzip $BACKUP_DIR/db_backup_$DATE.sql

# 删除30天前的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

#### 设置定时任务

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

---

## ⚙️ 配置说明

### 环境变量详解

#### 数据库配置

```bash
# 单独配置
DB_USER=novelgen              # 数据库用户名
DB_PASSWORD=secure_password   # 数据库密码（必须修改）
DB_NAME=novel_generator       # 数据库名称
DB_HOST=database              # 数据库主机（Docker服务名）
DB_PORT=5432                  # 数据库端口

# 或使用完整URL
DATABASE_URL=postgresql://user:password@host:port/database
```

#### 安全配置

```bash
# JWT密钥生成
python -c "import secrets; print(secrets.token_hex(32))"
# 或
openssl rand -hex 32

SECRET_KEY=生成的随机字符串
```

#### API配置

```bash
# OpenAI API
OPENAI_API_KEY=sk-...

# 如果使用代理
OPENAI_BASE_URL=https://your-proxy.com/v1
```

### Docker Compose配置

#### 修改端口

编辑 `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 将前端改为8080端口

  backend:
    ports:
      - "9000:8000"  # 将后端改为9000端口
```

#### 增加Workers

```yaml
backend:
  command: ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

#### 资源限制

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

---

## 🔧 常见问题

### Q1: 容器无法启动

```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend
docker-compose logs database

# 检查端口占用
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :80

# 重启服务
docker-compose restart
```

### Q2: 数据库连接失败

```bash
# 检查数据库是否ready
docker-compose ps

# 查看数据库日志
docker-compose logs database

# 手动测试连接
docker exec -it novel-generator-db psql -U novelgen -d novel_generator
```

### Q3: 前端无法访问后端API

检查 `nginx-site.conf` 中的代理配置:

```nginx
location /api/ {
    proxy_pass http://backend:8000;  # 确保指向正确的后端服务
}
```

### Q4: WebSocket连接失败

确保Nginx配置了WebSocket支持:

```nginx
location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
}
```

### Q5: 磁盘空间不足

```bash
# 清理Docker
docker system prune -a --volumes

# 清理日志
docker-compose logs --tail=1000 > recent_logs.txt
docker-compose down
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log
docker-compose up -d
```

---

## 📊 监控和维护

### 日志查看

```bash
# 实时查看所有日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看最近100行
docker-compose logs --tail=100 backend
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看特定容器
docker stats novel-generator-backend
```

### 数据库维护

```bash
# 进入数据库容器
docker exec -it novel-generator-db psql -U novelgen -d novel_generator

# 查看数据库大小
SELECT pg_size_pretty(pg_database_size('novel_generator'));

# 查看表大小
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# 清理和优化
VACUUM ANALYZE;
```

### 更新应用

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 检查状态
docker-compose ps
```

### 数据迁移

```bash
# 导出数据
docker exec novel-generator-db pg_dump -U novelgen novel_generator > backup.sql

# 导入到新服务器
cat backup.sql | docker exec -i novel-generator-db-new psql -U novelgen novel_generator
```

---

## 🔒 安全建议

1. **定期更新**: 及时更新Docker镜像和系统包
2. **强密码**: 使用强密码和随机SECRET_KEY
3. **防火墙**: 只开放必要的端口
4. **SSL/TLS**: 生产环境必须使用HTTPS
5. **备份**: 建立自动备份机制
6. **监控**: 设置日志监控和告警
7. **访问控制**: 使用VPN或IP白名单限制后台访问

---

## 📞 技术支持

- **文档**: https://github.com/yourusername/AI_NovelGenerator/wiki
- **Issue**: https://github.com/yourusername/AI_NovelGenerator/issues
- **讨论**: https://github.com/yourusername/AI_NovelGenerator/discussions

---

## 📄 许可证

本项目采用 MIT 许可证
