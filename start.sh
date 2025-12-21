#!/bin/bash
# AI Novel Generator - 本地快速启动脚本

set -e

echo "=================================="
echo "AI Novel Generator - 本地部署"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Docker是否安装
echo "🔍 检查环境..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装，请先安装Docker Desktop${NC}"
    echo "下载地址: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker已安装${NC}"

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker未运行，请启动Docker Desktop${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker正在运行${NC}"

# 检查.env文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env文件不存在，正在创建...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ 已创建.env文件${NC}"
    echo -e "${YELLOW}⚠️  请编辑.env文件，配置OPENAI_API_KEY等必要参数${NC}"
    echo ""
    echo "按Enter继续使用默认配置，或Ctrl+C退出编辑.env..."
    read
fi

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用 ($service)${NC}"
        echo "请停止占用该端口的服务，或修改docker-compose.yml中的端口映射"
        return 1
    fi
    return 0
}

echo ""
echo "🔍 检查端口占用..."
PORTS_OK=true
check_port 80 "Frontend" || PORTS_OK=false
check_port 8000 "Backend" || PORTS_OK=false
check_port 5432 "PostgreSQL" || PORTS_OK=false
check_port 6379 "Redis" || PORTS_OK=false
check_port 5672 "RabbitMQ" || PORTS_OK=false
check_port 15672 "RabbitMQ Management" || PORTS_OK=false
check_port 5555 "Flower" || PORTS_OK=false

if [ "$PORTS_OK" = false ]; then
    echo -e "${YELLOW}提示：可以修改docker-compose.yml中的端口映射来避免冲突${NC}"
    echo "是否继续启动？(y/N)"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✅ 端口检查完成${NC}"

# 询问启动模式
echo ""
echo "请选择启动模式："
echo "1) 完整模式 (所有服务，包括监控，需要约4GB内存)"
echo "2) 基础模式 (核心服务，需要约2GB内存)"
echo "3) 仅基础设施 (数据库、Redis、RabbitMQ)"
read -p "请输入选项 [1/2/3, 默认2]: " MODE
MODE=${MODE:-2}

echo ""
echo "🚀 开始启动服务..."

case $MODE in
    1)
        echo "启动完整模式（包括监控）..."
        docker-compose up -d
        docker-compose -f docker-compose.monitoring.yml up -d
        MONITORING=true
        ;;
    2)
        echo "启动基础模式..."
        docker-compose up -d database redis rabbitmq backend celery-worker celery-beat flower frontend
        MONITORING=false
        ;;
    3)
        echo "启动基础设施..."
        docker-compose up -d database redis rabbitmq
        MONITORING=false
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态："
docker-compose ps

# 等待后端健康检查
if [ "$MODE" != "3" ]; then
    echo ""
    echo "⏳ 等待后端服务就绪（最多60秒）..."
    COUNTER=0
    until curl -s http://localhost:8000/health > /dev/null 2>&1 || [ $COUNTER -eq 60 ]; do
        printf "."
        sleep 1
        ((COUNTER++))
    done
    echo ""

    if [ $COUNTER -eq 60 ]; then
        echo -e "${RED}❌ 后端服务启动超时${NC}"
        echo "请查看日志: docker-compose logs backend"
        exit 1
    fi

    echo -e "${GREEN}✅ 后端服务已就绪${NC}"
fi

# 显示访问信息
echo ""
echo "=================================="
echo -e "${GREEN}🎉 启动成功！${NC}"
echo "=================================="
echo ""
echo "📍 访问地址："
echo ""

if [ "$MODE" != "3" ]; then
    echo -e "${GREEN}前端界面:${NC}      http://localhost"
    echo -e "${GREEN}API文档:${NC}        http://localhost:8000/docs"
    echo -e "${GREEN}API接口:${NC}        http://localhost:8000"
    echo -e "${GREEN}Flower监控:${NC}     http://localhost:5555"
    echo -e "${GREEN}RabbitMQ管理:${NC}   http://localhost:15672 (admin/admin_password)"
fi

echo ""
echo "📊 数据库连接："
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: novel_generator"
echo "  User: novelgen"
echo "  Password: (见.env文件)"

if [ "$MONITORING" = true ]; then
    echo ""
    echo "📈 监控服务:"
    echo -e "${GREEN}Prometheus:${NC}     http://localhost:9090"
    echo -e "${GREEN}Grafana:${NC}        http://localhost:3001 (admin/admin)"
    echo -e "${GREEN}cAdvisor:${NC}       http://localhost:8080"
fi

echo ""
echo "📝 常用命令："
echo "  查看日志:     docker-compose logs -f"
echo "  查看后端日志: docker-compose logs -f backend"
echo "  停止服务:     docker-compose stop"
echo "  重启服务:     docker-compose restart"
echo "  停止并删除:   docker-compose down"
echo ""
echo "🆘 如遇问题，请查看 QUICKSTART.md 文档"
echo ""
echo -e "${GREEN}开始使用 AI Novel Generator 吧！🚀${NC}"
echo ""
