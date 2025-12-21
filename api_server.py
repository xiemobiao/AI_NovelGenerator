# api_server.py
# -*- coding: utf-8 -*-
"""
FastAPI服务器
提供RESTful API接口用于小说生成
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
from datetime import datetime
import asyncio
import uuid
import os

from logger_config import setup_logger, get_logger
from export_manager import export_novel

# 导入数据库和路由
from database import init_db
from auth_routes import router as auth_router
from version_routes import router as version_router
from websocket_routes import router as websocket_router

# 导入Prometheus监控
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import make_asgi_app
import prometheus_metrics

# 设置日志
logger = setup_logger("NovelAPI", log_dir="./logs")

# 创建FastAPI应用
app = FastAPI(
    title="AI Novel Generator API",
    description="AI驱动的小说生成服务API",
    version="1.5.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(version_router, prefix="/api/v1")
app.include_router(websocket_router)

# 配置Prometheus监控
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)

# 挂载Prometheus metrics端点（备用）
metrics_app = make_asgi_app()
app.mount("/prometheus", metrics_app)

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库和监控"""
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    # 启动系统指标收集
    import asyncio
    async def collect_metrics_periodically():
        while True:
            prometheus_metrics.collect_system_metrics()
            await asyncio.sleep(15)  # 每15秒收集一次

    asyncio.create_task(collect_metrics_periodically())
    logger.info("Prometheus监控已启动")

# 存储任务状态
tasks_status: Dict[str, Dict[str, Any]] = {}


# ==================== Pydantic模型定义 ====================

class NovelConfig(BaseModel):
    """小说生成配置"""
    topic: str = Field(..., description="小说主题")
    genre: str = Field(..., description="小说类型")
    num_chapters: int = Field(..., ge=1, le=500, description="章节数量")
    word_number: int = Field(..., ge=500, le=10000, description="每章字数")
    content_guidance: Optional[str] = Field(None, description="内容指导")
    core_characters: Optional[str] = Field(None, description="核心人物")
    key_items: Optional[str] = Field(None, description="关键道具")
    scenes: Optional[str] = Field(None, description="场景")
    time_constraints: Optional[str] = Field(None, description="时间约束")


class LLMConfig(BaseModel):
    """LLM配置"""
    interface_format: str = Field(..., description="接口格式")
    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    model_name: str = Field(..., description="模型名称")
    temperature: float = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(4096, ge=100, le=32000, description="最大tokens")
    timeout: int = Field(600, ge=30, le=3600, description="超时时间(秒)")


class EmbeddingConfig(BaseModel):
    """Embedding配置"""
    interface_format: str = Field(..., description="接口格式")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    model_name: str = Field(..., description="模型名称")
    retrieval_k: int = Field(4, ge=1, le=20, description="检索数量")


class GenerationRequest(BaseModel):
    """生成请求"""
    novel_config: NovelConfig
    llm_config: LLMConfig
    embedding_config: EmbeddingConfig
    output_dir: str = Field(..., description="输出目录")
    project_name: Optional[str] = Field(None, description="项目名称")


class ChapterGenerationRequest(BaseModel):
    """章节生成请求"""
    project_id: str = Field(..., description="项目ID")
    chapter_number: int = Field(..., ge=1, description="章节号")
    chapter_guidance: Optional[str] = Field(None, description="本章指导")


class ExportRequest(BaseModel):
    """导出请求"""
    project_id: str = Field(..., description="项目ID")
    format: str = Field(..., description="导出格式 (txt/epub/pdf/docx)")
    title: Optional[str] = Field(None, description="小说标题")
    author: Optional[str] = Field("AI Novel Generator", description="作者")
    num_chapters: Optional[int] = Field(None, description="导出章节数")


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: float = 0.0  # 0-100
    message: str = ""
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ==================== 辅助函数 ====================

def create_task(task_type: str, description: str) -> str:
    """创建新任务"""
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    tasks_status[task_id] = {
        "task_id": task_id,
        "type": task_type,
        "status": "pending",
        "progress": 0.0,
        "message": description,
        "created_at": now,
        "updated_at": now,
        "result": None,
        "error": None
    }

    logger.info(f"创建任务: {task_id} - {task_type} - {description}")
    return task_id


def update_task(task_id: str, status: str = None, progress: float = None,
                message: str = None, result: Dict = None, error: str = None):
    """更新任务状态"""
    if task_id not in tasks_status:
        return

    task = tasks_status[task_id]

    if status:
        task["status"] = status
    if progress is not None:
        task["progress"] = progress
    if message:
        task["message"] = message
    if result is not None:
        task["result"] = result
    if error:
        task["error"] = error

    task["updated_at"] = datetime.now().isoformat()


async def generate_architecture_async(task_id: str, request: GenerationRequest):
    """异步生成小说架构"""
    try:
        update_task(task_id, status="running", progress=10, message="初始化生成器...")

        # 导入生成模块
        from novel_generator import Novel_architecture_generate
        from llm_adapters import create_llm_adapter

        update_task(task_id, progress=20, message="创建LLM适配器...")

        # 创建LLM适配器
        llm = create_llm_adapter(
            interface_format=request.llm_config.interface_format,
            api_key=request.llm_config.api_key,
            base_url=request.llm_config.base_url,
            model_name=request.llm_config.model_name,
            temperature=request.llm_config.temperature,
            max_tokens=request.llm_config.max_tokens,
            timeout=request.llm_config.timeout
        )

        update_task(task_id, progress=30, message="生成小说架构...")

        # 生成架构
        output_dir = Path(request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        result = await asyncio.to_thread(
            Novel_architecture_generate,
            llm=llm,
            topic=request.novel_config.topic,
            genre=request.novel_config.genre,
            num_chapters=request.novel_config.num_chapters,
            word_number=request.novel_config.word_number,
            filepath=str(output_dir),
            content_guidance=request.novel_config.content_guidance,
            core_characters=request.novel_config.core_characters,
            key_items=request.novel_config.key_items,
            scenes=request.novel_config.scenes,
            time_constraints=request.novel_config.time_constraints
        )

        update_task(
            task_id,
            status="completed",
            progress=100,
            message="架构生成完成",
            result={"architecture_file": str(output_dir / "Novel_architecture.txt")}
        )

    except Exception as e:
        logger.error(f"生成架构失败: {e}", exc_info=True)
        update_task(
            task_id,
            status="failed",
            message="生成失败",
            error=str(e)
        )


# ==================== API端点 ====================

@app.get("/", tags=["基础"])
async def root():
    """API根路径"""
    return {
        "message": "AI Novel Generator API",
        "version": "1.5.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["基础"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len([t for t in tasks_status.values() if t["status"] == "running"])
    }


@app.post("/api/v1/novel/architecture", tags=["生成"], response_model=Dict[str, str])
async def create_architecture(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    生成小说架构（Step1）

    创建一个后台任务来生成小说架构，包括：
    - 核心故事种子
    - 角色动力学
    - 世界观构建
    - 情节架构
    - 初始角色状态
    """
    task_id = create_task("architecture", "生成小说架构")

    background_tasks.add_task(generate_architecture_async, task_id, request)

    return {
        "task_id": task_id,
        "message": "架构生成任务已创建",
        "status_url": f"/api/v1/task/{task_id}"
    }


@app.post("/api/v1/novel/blueprint", tags=["生成"])
async def create_blueprint(request: GenerationRequest, background_tasks: BackgroundTasks):
    """生成章节目录（Step2）"""
    # TODO: 实现章节目录生成
    task_id = create_task("blueprint", "生成章节目录")
    return {"task_id": task_id, "message": "功能开发中"}


@app.post("/api/v1/novel/chapter", tags=["生成"])
async def generate_chapter(request: ChapterGenerationRequest, background_tasks: BackgroundTasks):
    """生成章节草稿（Step3）"""
    # TODO: 实现章节生成
    task_id = create_task("chapter", f"生成第{request.chapter_number}章")
    return {"task_id": task_id, "message": "功能开发中"}


@app.post("/api/v1/novel/finalize", tags=["生成"])
async def finalize_chapter(request: ChapterGenerationRequest, background_tasks: BackgroundTasks):
    """定稿章节（Step4）"""
    # TODO: 实现章节定稿
    task_id = create_task("finalize", f"定稿第{request.chapter_number}章")
    return {"task_id": task_id, "message": "功能开发中"}


@app.post("/api/v1/novel/export", tags=["导出"])
async def export_novel_api(request: ExportRequest):
    """
    导出小说

    支持的格式：
    - txt: 纯文本
    - epub: 电子书格式
    - pdf: PDF文档
    - docx: Word文档
    """
    try:
        # 构建项目路径
        project_dir = Path(request.project_id)

        if not project_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {request.project_id}"
            )

        # 确定输出文件
        output_file = project_dir / f"novel.{request.format}"

        # 执行导出
        success = await asyncio.to_thread(
            export_novel,
            novel_dir=str(project_dir),
            output_file=str(output_file),
            format_type=request.format,
            title=request.title,
            author=request.author,
            num_chapters=request.num_chapters
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="导出失败"
            )

        return {
            "message": "导出成功",
            "file": str(output_file),
            "format": request.format
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/task/{task_id}", tags=["任务"], response_model=TaskStatus)
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )

    return tasks_status[task_id]


@app.get("/api/v1/tasks", tags=["任务"])
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    """列出所有任务"""
    tasks = list(tasks_status.values())

    if status:
        tasks = [t for t in tasks if t["status"] == status]

    # 按创建时间倒序
    tasks.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "total": len(tasks),
        "tasks": tasks[:limit]
    }


@app.delete("/api/v1/task/{task_id}", tags=["任务"])
async def delete_task(task_id: str):
    """删除任务记录"""
    if task_id not in tasks_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )

    # 不允许删除正在运行的任务
    if tasks_status[task_id]["status"] == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除正在运行的任务"
        )

    del tasks_status[task_id]
    return {"message": "任务已删除"}


@app.get("/api/v1/projects", tags=["项目"])
async def list_projects(base_dir: str = "."):
    """列出所有项目"""
    try:
        base_path = Path(base_dir)
        projects = []

        for item in base_path.iterdir():
            if item.is_dir():
                # 检查是否包含小说文件
                has_architecture = (item / "Novel_architecture.txt").exists()
                has_directory = (item / "Novel_directory.txt").exists()

                if has_architecture or has_directory:
                    # 统计章节数
                    chapters = list(item.glob("chapter_*.txt"))

                    projects.append({
                        "id": str(item),
                        "name": item.name,
                        "has_architecture": has_architecture,
                        "has_directory": has_directory,
                        "chapter_count": len(chapters),
                        "created_at": datetime.fromtimestamp(
                            item.stat().st_ctime
                        ).isoformat()
                    })

        return {"total": len(projects), "projects": projects}

    except Exception as e:
        logger.error(f"列出项目失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn

    # 运行服务器
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
