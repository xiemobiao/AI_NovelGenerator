@echo off
REM AI Novel Generator - Windows本地快速启动脚本

echo ==================================
echo AI Novel Generator - 本地部署
echo ==================================
echo.

REM 检查Docker是否安装
echo 🔍 检查环境...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Docker已安装

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行，请启动Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker正在运行

REM 检查.env文件
if not exist .env (
    echo ⚠️  .env文件不存在，正在创建...
    copy .env.example .env
    echo ✅ 已创建.env文件
    echo ⚠️  请编辑.env文件，配置OPENAI_API_KEY等必要参数
    echo.
    echo 按任意键继续使用默认配置...
    pause >nul
)

echo.
echo 请选择启动模式：
echo 1) 完整模式 (所有服务，包括监控，需要约4GB内存)
echo 2) 基础模式 (核心服务，需要约2GB内存)
echo 3) 仅基础设施 (数据库、Redis、RabbitMQ)
set /p MODE="请输入选项 [1/2/3, 默认2]: "
if "%MODE%"=="" set MODE=2

echo.
echo 🚀 开始启动服务...

if "%MODE%"=="1" (
    echo 启动完整模式（包括监控）...
    docker-compose up -d
    docker-compose -f docker-compose.monitoring.yml up -d
    set MONITORING=true
) else if "%MODE%"=="2" (
    echo 启动基础模式...
    docker-compose up -d database redis rabbitmq backend celery-worker celery-beat flower frontend
    set MONITORING=false
) else if "%MODE%"=="3" (
    echo 启动基础设施...
    docker-compose up -d database redis rabbitmq
    set MONITORING=false
) else (
    echo ❌ 无效选项
    pause
    exit /b 1
)

echo.
echo ⏳ 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo.
echo 📊 服务状态：
docker-compose ps

REM 等待后端健康检查
if not "%MODE%"=="3" (
    echo.
    echo ⏳ 等待后端服务就绪（最多60秒）...
    set COUNTER=0
    :wait_loop
    curl -s http://localhost:8000/health >nul 2>&1
    if %errorlevel% equ 0 goto backend_ready
    if %COUNTER% geq 60 goto backend_timeout
    timeout /t 1 /nobreak >nul
    set /a COUNTER+=1
    echo|set /p="."
    goto wait_loop

    :backend_timeout
    echo.
    echo ❌ 后端服务启动超时
    echo 请查看日志: docker-compose logs backend
    pause
    exit /b 1

    :backend_ready
    echo.
    echo ✅ 后端服务已就绪
)

REM 显示访问信息
echo.
echo ==================================
echo 🎉 启动成功！
echo ==================================
echo.
echo 📍 访问地址：
echo.

if not "%MODE%"=="3" (
    echo 前端界面:      http://localhost
    echo API文档:        http://localhost:8000/docs
    echo API接口:        http://localhost:8000
    echo Flower监控:     http://localhost:5555
    echo RabbitMQ管理:   http://localhost:15672 (admin/admin_password)
)

echo.
echo 📊 数据库连接：
echo   Host: localhost
echo   Port: 5432
echo   Database: novel_generator
echo   User: novelgen
echo   Password: (见.env文件)

if "%MONITORING%"=="true" (
    echo.
    echo 📈 监控服务:
    echo Prometheus:     http://localhost:9090
    echo Grafana:        http://localhost:3001 (admin/admin)
    echo cAdvisor:       http://localhost:8080
)

echo.
echo 📝 常用命令：
echo   查看日志:     docker-compose logs -f
echo   查看后端日志: docker-compose logs -f backend
echo   停止服务:     docker-compose stop
echo   重启服务:     docker-compose restart
echo   停止并删除:   docker-compose down
echo.
echo 🆘 如遇问题，请查看 QUICKSTART.md 文档
echo.
echo 开始使用 AI Novel Generator 吧！🚀
echo.
pause
