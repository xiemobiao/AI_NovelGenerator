# api_server.py
# -*- coding: utf-8 -*-
"""
FastAPI服务器
提供RESTful API接口用于小说生成
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, status, File, Form, UploadFile
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

# 导入Sentry错误追踪
from sentry_config import init_sentry

# 设置日志
logger = setup_logger("NovelAPI", log_dir="./logs")

# 初始化Sentry
init_sentry()

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
    filepath: str = Field(..., description="项目路径")
    chapter_num: int = Field(..., ge=1, description="章节号")
    word_number: int = Field(3000, ge=500, le=10000, description="字数")
    characters_involved: Optional[str] = Field(None, description="涉及角色")
    key_items: Optional[str] = Field(None, description="关键物品")
    scene_location: Optional[str] = Field(None, description="场景地点")
    time_constraint: Optional[str] = Field(None, description="时间限制")
    user_guidance: Optional[str] = Field(None, description="剧情指导")


class ChapterFinalizeRequest(BaseModel):
    """章节定稿请求"""
    filepath: str = Field(..., description="项目路径")
    chapter_num: int = Field(..., ge=1, description="章节号")
    word_number: int = Field(3000, ge=500, le=10000, description="字数")


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


class AppConfig(BaseModel):
    """应用配置"""
    llm: LLMConfig
    embedding: EmbeddingConfig
    other_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他参数")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    llm: Optional[LLMConfig] = None
    embedding: Optional[EmbeddingConfig] = None
    other_params: Optional[Dict[str, Any]] = None


# ==================== 辅助函数 ====================

def load_project_config(filepath: str) -> Dict[str, Any]:
    """
    加载项目配置，包括LLM和Embedding配置

    优先级：
    1. 项目目录下的config.json
    2. 环境变量
    3. 默认配置
    """
    import json

    config = {
        "llm": {
            "interface_format": os.getenv("LLM_INTERFACE_FORMAT", "openai"),
            "api_key": os.getenv("LLM_API_KEY", ""),
            "base_url": os.getenv("LLM_BASE_URL", ""),
            "model_name": os.getenv("LLM_MODEL_NAME", "gpt-4o-mini"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
            "timeout": int(os.getenv("LLM_TIMEOUT", "600"))
        },
        "embedding": {
            "interface_format": os.getenv("EMBEDDING_INTERFACE_FORMAT", "openai"),
            "api_key": os.getenv("EMBEDDING_API_KEY", ""),
            "base_url": os.getenv("EMBEDDING_BASE_URL", ""),
            "model_name": os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small"),
            "retrieval_k": int(os.getenv("EMBEDDING_RETRIEVAL_K", "4"))
        }
    }

    # 尝试从项目配置文件加载
    config_file = Path(filepath) / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
                if "llm" in project_config:
                    config["llm"].update(project_config["llm"])
                if "embedding" in project_config:
                    config["embedding"].update(project_config["embedding"])
        except Exception as e:
            logger.warning(f"加载项目配置失败: {e}")

    return config


# 全局配置文件路径
GLOBAL_CONFIG_FILE = Path("./config.json")


# 模型提供商预设配置
MODEL_PROVIDER_PRESETS = {
    "openai": {
        "name": "OpenAI",
        "llm": {
            "interface_format": "openai",
            "base_url": "https://api.openai.com/v1",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "default_model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 600
        },
        "embedding": {
            "interface_format": "openai",
            "base_url": "https://api.openai.com/v1",
            "models": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
            "default_model": "text-embedding-3-small",
            "retrieval_k": 4
        }
    },
    "openrouter": {
        "name": "OpenRouter",
        "llm": {
            "interface_format": "openrouter",
            "base_url": "https://openrouter.ai/api/v1",
            "models": [
                "anthropic/claude-3.5-sonnet",
                "google/gemini-pro-1.5",
                "openai/gpt-4o",
                "meta-llama/llama-3.1-70b-instruct",
                "mistralai/mistral-large"
            ],
            "default_model": "anthropic/claude-3.5-sonnet",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 600
        },
        "embedding": {
            "interface_format": "openai",
            "base_url": "https://openrouter.ai/api/v1",
            "models": ["openai/text-embedding-3-small"],
            "default_model": "openai/text-embedding-3-small",
            "retrieval_k": 4
        }
    },
    "azure": {
        "name": "Azure OpenAI",
        "llm": {
            "interface_format": "azure",
            "base_url": "https://YOUR-RESOURCE-NAME.openai.azure.com",
            "models": ["gpt-4", "gpt-35-turbo"],
            "default_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 600
        },
        "embedding": {
            "interface_format": "azure",
            "base_url": "https://YOUR-RESOURCE-NAME.openai.azure.com",
            "models": ["text-embedding-ada-002"],
            "default_model": "text-embedding-ada-002",
            "retrieval_k": 4
        }
    },
    "gemini": {
        "name": "Google Gemini",
        "llm": {
            "interface_format": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "default_model": "gemini-1.5-flash",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 600
        },
        "embedding": {
            "interface_format": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "models": ["text-embedding-004"],
            "default_model": "text-embedding-004",
            "retrieval_k": 4
        }
    },
    "claude": {
        "name": "Anthropic Claude",
        "llm": {
            "interface_format": "claude",
            "base_url": "https://api.anthropic.com/v1",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "default_model": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 600
        },
        "embedding": {
            "interface_format": "openai",
            "base_url": "https://api.openai.com/v1",
            "models": ["text-embedding-3-small"],
            "default_model": "text-embedding-3-small",
            "retrieval_k": 4,
            "note": "Claude不提供embedding服务，建议使用OpenAI"
        }
    },
    "deepseek": {
        "name": "DeepSeek",
        "llm": {
            "interface_format": "openai",
            "base_url": "https://api.deepseek.com/v1",
            "models": ["deepseek-chat", "deepseek-coder"],
            "default_model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 600
        },
        "embedding": {
            "interface_format": "openai",
            "base_url": "https://api.openai.com/v1",
            "models": ["text-embedding-3-small"],
            "default_model": "text-embedding-3-small",
            "retrieval_k": 4,
            "note": "DeepSeek不提供embedding服务，建议使用OpenAI"
        }
    },
    "moonshot": {
        "name": "Moonshot (月之暗面)",
        "llm": {
            "interface_format": "openai",
            "base_url": "https://api.moonshot.cn/v1",
            "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
            "default_model": "moonshot-v1-8k",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 600
        },
        "embedding": {
            "interface_format": "openai",
            "base_url": "https://api.openai.com/v1",
            "models": ["text-embedding-3-small"],
            "default_model": "text-embedding-3-small",
            "retrieval_k": 4,
            "note": "Moonshot不提供embedding服务，建议使用OpenAI"
        }
    },
    "zhipu": {
        "name": "智谱AI (GLM)",
        "llm": {
            "interface_format": "openai",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "models": ["glm-4", "glm-4-flash", "glm-3-turbo"],
            "default_model": "glm-4-flash",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 600
        },
        "embedding": {
            "interface_format": "openai",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "models": ["embedding-2"],
            "default_model": "embedding-2",
            "retrieval_k": 4
        }
    }
}


def load_global_config() -> Dict[str, Any]:
    """
    加载全局配置文件

    Returns:
        配置字典，包含llm、embedding和other_params
    """
    import json

    default_config = {
        "llm": {
            "interface_format": os.getenv("LLM_INTERFACE_FORMAT", "openai"),
            "api_key": os.getenv("LLM_API_KEY", ""),
            "base_url": os.getenv("LLM_BASE_URL", ""),
            "model_name": os.getenv("LLM_MODEL_NAME", "gpt-4o-mini"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
            "timeout": int(os.getenv("LLM_TIMEOUT", "600"))
        },
        "embedding": {
            "interface_format": os.getenv("EMBEDDING_INTERFACE_FORMAT", "openai"),
            "api_key": os.getenv("EMBEDDING_API_KEY", ""),
            "base_url": os.getenv("EMBEDDING_BASE_URL", ""),
            "model_name": os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small"),
            "retrieval_k": int(os.getenv("EMBEDDING_RETRIEVAL_K", "4"))
        },
        "other_params": {}
    }

    if GLOBAL_CONFIG_FILE.exists():
        try:
            with open(GLOBAL_CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # 合并配置
                if "llm" in file_config:
                    default_config["llm"].update(file_config["llm"])
                if "embedding" in file_config:
                    default_config["embedding"].update(file_config["embedding"])
                if "other_params" in file_config:
                    default_config["other_params"] = file_config["other_params"]
        except Exception as e:
            logger.warning(f"加载全局配置失败: {e}")

    return default_config


def save_global_config(config: Dict[str, Any]) -> bool:
    """
    保存全局配置到文件

    Args:
        config: 配置字典

    Returns:
        是否成功
    """
    import json

    try:
        with open(GLOBAL_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存到 {GLOBAL_CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}", exc_info=True)
        return False


def parse_blueprint_file(filepath: str) -> List[Dict]:
    """
    解析Novel_directory.txt文件，提取章节蓝图信息

    返回格式：
    [
        {
            "chapter_number": 1,
            "title": "章节标题",
            "summary": "内容摘要",
            "key_events": ["事件1", "事件2"],
            "characters": ["角色1", "角色2"]
        },
        ...
    ]
    """
    import re

    blueprint_file = Path(filepath) / "Novel_directory.txt"
    if not blueprint_file.exists():
        return []

    try:
        with open(blueprint_file, 'r', encoding='utf-8') as f:
            content = f.read()

        blueprints = []
        # 使用正则表达式分割章节
        chapter_pattern = r'第\s*(\d+)\s*章[：:](.*?)(?=第\s*\d+\s*章|$)'
        matches = re.findall(chapter_pattern, content, re.DOTALL)

        for match in matches:
            chapter_num = int(match[0])
            chapter_content = match[1].strip()

            # 提取标题（第一行）
            lines = chapter_content.split('\n')
            title = lines[0].strip() if lines else ""

            # 提取摘要和其他信息
            summary = ""
            key_events = []
            characters = []

            for line in lines[1:]:
                line = line.strip()
                if line.startswith("摘要") or line.startswith("内容"):
                    summary = line.split(':', 1)[-1].strip() if ':' in line else line
                elif line.startswith("关键事件") or line.startswith("事件"):
                    # 可能有多个事件列出
                    events_text = line.split(':', 1)[-1].strip() if ':' in line else ""
                    if events_text:
                        key_events = [e.strip() for e in events_text.split('、') if e.strip()]
                elif line.startswith("角色") or line.startswith("人物"):
                    chars_text = line.split(':', 1)[-1].strip() if ':' in line else ""
                    if chars_text:
                        characters = [c.strip() for c in chars_text.split('、') if c.strip()]

            blueprints.append({
                "chapter_number": chapter_num,
                "title": title,
                "summary": summary or chapter_content[:200],  # 如果没有摘要，取前200字
                "key_events": key_events,
                "characters": characters
            })

        return sorted(blueprints, key=lambda x: x["chapter_number"])

    except Exception as e:
        logger.error(f"解析蓝图文件失败: {e}", exc_info=True)
        return []


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

        update_task(task_id, progress=30, message="生成小说架构...")

        # 生成架构
        output_dir = Path(request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        result = await asyncio.to_thread(
            Novel_architecture_generate,
            interface_format=request.llm_config.interface_format,
            api_key=request.llm_config.api_key,
            base_url=request.llm_config.base_url,
            llm_model=request.llm_config.model_name,
            topic=request.novel_config.topic,
            genre=request.novel_config.genre,
            number_of_chapters=request.novel_config.num_chapters,
            word_number=request.novel_config.word_number,
            filepath=str(output_dir),
            user_guidance=request.novel_config.content_guidance or "",
            temperature=request.llm_config.temperature,
            max_tokens=request.llm_config.max_tokens,
            timeout=request.llm_config.timeout
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


async def generate_blueprint_async(task_id: str, request: GenerationRequest):
    """异步生成章节蓝图"""
    try:
        update_task(task_id, status="running", progress=10, message="初始化蓝图生成...")

        # 导入生成模块
        from novel_generator import Chapter_blueprint_generate

        update_task(task_id, progress=30, message="生成章节蓝图...")

        # 生成蓝图
        output_dir = Path(request.output_dir)
        if not output_dir.exists():
            raise ValueError(f"项目目录不存在: {output_dir}")

        arch_file = output_dir / "Novel_architecture.txt"
        if not arch_file.exists():
            raise ValueError("请先生成小说架构")

        result = await asyncio.to_thread(
            Chapter_blueprint_generate,
            interface_format=request.llm_config.interface_format,
            api_key=request.llm_config.api_key,
            base_url=request.llm_config.base_url,
            llm_model=request.llm_config.model_name,
            filepath=str(output_dir),
            number_of_chapters=request.novel_config.num_chapters,
            user_guidance=request.novel_config.content_guidance or "",
            temperature=request.llm_config.temperature,
            max_tokens=request.llm_config.max_tokens,
            timeout=request.llm_config.timeout
        )

        update_task(
            task_id,
            status="completed",
            progress=100,
            message="蓝图生成完成",
            result={"blueprint_file": str(output_dir / "Novel_directory.txt")}
        )

    except Exception as e:
        logger.error(f"生成蓝图失败: {e}", exc_info=True)
        update_task(
            task_id,
            status="failed",
            message="生成失败",
            error=str(e)
        )


async def generate_chapter_async(task_id: str, chapter_req: ChapterGenerationRequest):
    """异步生成章节草稿"""
    try:
        update_task(task_id, status="running", progress=10, message="初始化章节生成...")

        # 加载项目配置
        config = load_project_config(chapter_req.filepath)

        # 导入生成模块
        from novel_generator import generate_chapter_draft

        update_task(task_id, progress=30, message=f"生成第{chapter_req.chapter_num}章...")

        # 确保chapters目录存在
        project_dir = Path(chapter_req.filepath)
        chapters_dir = project_dir / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        result = await asyncio.to_thread(
            generate_chapter_draft,
            api_key=config["llm"]["api_key"],
            base_url=config["llm"]["base_url"],
            model_name=config["llm"]["model_name"],
            filepath=str(project_dir),
            novel_number=chapter_req.chapter_num,
            word_number=chapter_req.word_number,
            temperature=config["llm"]["temperature"],
            user_guidance=chapter_req.user_guidance or "",
            characters_involved=chapter_req.characters_involved or "",
            key_items=chapter_req.key_items or "",
            scene_location=chapter_req.scene_location or "",
            time_constraint=chapter_req.time_constraint or "",
            embedding_api_key=config["embedding"]["api_key"],
            embedding_url=config["embedding"]["base_url"],
            embedding_interface_format=config["embedding"]["interface_format"],
            embedding_model_name=config["embedding"]["model_name"],
            embedding_retrieval_k=config["embedding"]["retrieval_k"],
            interface_format=config["llm"]["interface_format"],
            max_tokens=config["llm"]["max_tokens"],
            timeout=config["llm"]["timeout"]
        )

        chapter_file = chapters_dir / f"chapter_{chapter_req.chapter_num}.txt"

        update_task(
            task_id,
            status="completed",
            progress=100,
            message="章节生成完成",
            result={
                "chapter_number": chapter_req.chapter_num,
                "chapter_file": str(chapter_file)
            }
        )

    except Exception as e:
        logger.error(f"生成章节失败: {e}", exc_info=True)
        update_task(
            task_id,
            status="failed",
            message="生成失败",
            error=str(e)
        )


async def finalize_chapter_async(task_id: str, finalize_req: ChapterFinalizeRequest):
    """异步定稿章节"""
    try:
        update_task(task_id, status="running", progress=10, message="初始化章节定稿...")

        # 加载项目配置
        config = load_project_config(finalize_req.filepath)

        # 导入定稿模块
        from novel_generator import finalize_chapter

        update_task(task_id, progress=30, message=f"定稿第{finalize_req.chapter_num}章...")

        project_dir = Path(finalize_req.filepath)

        result = await asyncio.to_thread(
            finalize_chapter,
            novel_number=finalize_req.chapter_num,
            word_number=finalize_req.word_number,
            api_key=config["llm"]["api_key"],
            base_url=config["llm"]["base_url"],
            model_name=config["llm"]["model_name"],
            temperature=config["llm"]["temperature"],
            filepath=str(project_dir),
            embedding_api_key=config["embedding"]["api_key"],
            embedding_url=config["embedding"]["base_url"],
            embedding_interface_format=config["embedding"]["interface_format"],
            embedding_model_name=config["embedding"]["model_name"],
            interface_format=config["llm"]["interface_format"],
            max_tokens=config["llm"]["max_tokens"],
            timeout=config["llm"]["timeout"]
        )

        update_task(
            task_id,
            status="completed",
            progress=100,
            message="章节定稿完成",
            result={
                "chapter_number": finalize_req.chapter_num,
                "message": "已更新前文摘要和角色状态"
            }
        )

    except Exception as e:
        logger.error(f"定稿章节失败: {e}", exc_info=True)
        update_task(
            task_id,
            status="failed",
            message="定稿失败",
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


@app.post("/api/v1/novel/blueprint", tags=["生成"], response_model=Dict[str, str])
async def create_blueprint(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    生成章节蓝图（Step2）

    创建一个后台任务来生成章节目录，包括每一章的：
    - 章节标题
    - 内容摘要
    - 关键事件
    - 涉及角色
    """
    task_id = create_task("blueprint", "生成章节蓝图")

    background_tasks.add_task(generate_blueprint_async, task_id, request)

    return {
        "task_id": task_id,
        "message": "蓝图生成任务已创建",
        "status_url": f"/api/v1/task/{task_id}"
    }


@app.get("/api/v1/novel/blueprint", tags=["查询"])
async def get_blueprint(filepath: str):
    """
    获取章节蓝图列表

    从Novel_directory.txt文件中读取并解析章节蓝图信息

    Args:
        filepath: 项目目录路径

    Returns:
        章节蓝图列表
    """
    try:
        project_dir = Path(filepath)
        if not project_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目目录不存在: {filepath}"
            )

        blueprints = parse_blueprint_file(filepath)

        return {
            "total": len(blueprints),
            "blueprints": blueprints
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取蓝图失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/novel/chapter/draft", tags=["生成"], response_model=Dict[str, str])
async def generate_chapter_draft(
    request: ChapterGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    生成章节草稿（Step3）

    创建一个后台任务来生成章节内容，包括：
    - 读取小说架构和章节蓝图
    - 检索相关知识库上下文
    - 生成章节草稿文本
    """
    try:
        project_dir = Path(request.filepath)
        if not project_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目目录不存在: {request.filepath}"
            )

        task_id = create_task("chapter", f"生成第{request.chapter_num}章草稿")

        background_tasks.add_task(generate_chapter_async, task_id, request)

        return {
            "task_id": task_id,
            "message": "章节生成任务已创建",
            "status_url": f"/api/v1/task/{task_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建章节生成任务失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/novel/chapter/finalize", tags=["生成"], response_model=Dict[str, str])
async def finalize_chapter_endpoint(
    request: ChapterFinalizeRequest,
    background_tasks: BackgroundTasks
):
    """
    定稿章节（Step4）

    创建一个后台任务来定稿章节，包括：
    - 更新前文摘要
    - 更新角色状态
    - 将章节内容存入向量库
    """
    try:
        project_dir = Path(request.filepath)
        if not project_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目目录不存在: {request.filepath}"
            )

        chapter_file = project_dir / "chapters" / f"chapter_{request.chapter_num}.txt"
        if not chapter_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"章节文件不存在，请先生成章节草稿"
            )

        task_id = create_task("finalize", f"定稿第{request.chapter_num}章")

        background_tasks.add_task(finalize_chapter_async, task_id, request)

        return {
            "task_id": task_id,
            "message": "定稿任务已创建",
            "status_url": f"/api/v1/task/{task_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建定稿任务失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/novel/chapters", tags=["查询"])
async def list_chapters(filepath: str):
    """
    列出所有章节

    返回项目中所有已生成的章节列表
    """
    try:
        project_dir = Path(filepath)
        if not project_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目目录不存在: {filepath}"
            )

        chapters_dir = project_dir / "chapters"
        if not chapters_dir.exists():
            return {"total": 0, "chapters": []}

        chapters = []
        for chapter_file in sorted(chapters_dir.glob("chapter_*.txt")):
            # 从文件名提取章节号
            filename = chapter_file.stem  # chapter_1
            try:
                chapter_num = int(filename.split('_')[1])

                # 读取章节内容
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取标题（第一行）
                lines = content.split('\n')
                title = lines[0].strip() if lines else ""

                # 计算字数
                word_count = len(content)

                # 判断状态（简化处理，如果存在向量库记录则为final）
                status_value = "draft"  # 默认为草稿

                chapters.append({
                    "chapter_number": chapter_num,
                    "title": title or f"第{chapter_num}章",
                    "word_count": word_count,
                    "status": status_value,
                    "content": content[:200] + "..." if len(content) > 200 else content  # 预览
                })
            except (ValueError, IndexError):
                continue

        return {
            "total": len(chapters),
            "chapters": sorted(chapters, key=lambda x: x["chapter_number"])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"列出章节失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/novel/chapter", tags=["查询"])
async def get_chapter(filepath: str, chapter_num: int):
    """
    获取单个章节的完整内容

    Args:
        filepath: 项目路径
        chapter_num: 章节号
    """
    try:
        project_dir = Path(filepath)
        chapter_file = project_dir / "chapters" / f"chapter_{chapter_num}.txt"

        if not chapter_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"章节 {chapter_num} 不存在"
            )

        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取标题
        lines = content.split('\n')
        title = lines[0].strip() if lines else ""

        return {
            "chapter_number": chapter_num,
            "title": title or f"第{chapter_num}章",
            "content": content,
            "word_count": len(content),
            "status": "draft"  # 简化处理
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.put("/api/v1/novel/chapter", tags=["编辑"])
async def update_chapter(
    filepath: str,
    chapter_num: int,
    content: str
):
    """
    更新章节内容

    Args:
        filepath: 项目路径
        chapter_num: 章节号
        content: 新的章节内容
    """
    try:
        project_dir = Path(filepath)
        chapters_dir = project_dir / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        chapter_file = chapters_dir / f"chapter_{chapter_num}.txt"

        # 保存新内容
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"章节 {chapter_num} 已更新")

        return {
            "message": "章节更新成功",
            "chapter_number": chapter_num,
            "word_count": len(content)
        }

    except Exception as e:
        logger.error(f"更新章节失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/novel/architecture", tags=["查询"])
async def get_architecture(filepath: str):
    """
    获取小说架构

    读取并返回Novel_architecture.txt的内容
    """
    try:
        project_dir = Path(filepath)
        arch_file = project_dir / "Novel_architecture.txt"

        if not arch_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="小说架构不存在，请先生成架构"
            )

        with open(arch_file, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "content": content,
            "file_path": str(arch_file)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取架构失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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


@app.get("/api/v1/config", tags=["配置"], response_model=AppConfig)
async def get_config():
    """
    获取全局配置

    返回当前的LLM、Embedding和其他参数配置
    """
    try:
        config = load_global_config()
        return AppConfig(**config)
    except Exception as e:
        logger.error(f"获取配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.put("/api/v1/config", tags=["配置"])
async def update_config(request: ConfigUpdateRequest):
    """
    更新全局配置

    Args:
        request: 配置更新请求（可以只更新部分配置）
    """
    try:
        # 加载现有配置
        current_config = load_global_config()

        # 更新配置
        if request.llm:
            current_config["llm"].update(request.llm.model_dump(exclude_none=True))

        if request.embedding:
            current_config["embedding"].update(request.embedding.model_dump(exclude_none=True))

        if request.other_params:
            current_config["other_params"].update(request.other_params)

        # 保存配置
        if save_global_config(current_config):
            return {
                "message": "配置更新成功",
                "config": current_config
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存配置失败"
            )

    except Exception as e:
        logger.error(f"更新配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/config/test-llm", tags=["配置"])
async def test_llm_config(llm_config: LLMConfig):
    """
    测试LLM配置是否可用

    Args:
        llm_config: LLM配置参数

    Returns:
        测试结果
    """
    try:
        from llm_adapters import create_llm_adapter

        logger.info("开始测试LLM配置...")

        # 创建LLM适配器
        llm_adapter = create_llm_adapter(
            interface_format=llm_config.interface_format,
            base_url=llm_config.base_url or "",
            model_name=llm_config.model_name,
            api_key=llm_config.api_key,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
            timeout=llm_config.timeout
        )

        # 发送测试请求
        test_prompt = "Please reply 'OK' to confirm the connection."
        response = await asyncio.to_thread(llm_adapter.invoke, test_prompt)

        if response and len(response.strip()) > 0:
            logger.info(f"LLM配置测试成功，响应: {response[:100]}")
            return {
                "success": True,
                "message": "LLM配置测试成功",
                "response": response[:200]  # 返回前200字符
            }
        else:
            return {
                "success": False,
                "message": "LLM返回空响应"
            }

    except Exception as e:
        logger.error(f"LLM配置测试失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }


@app.post("/api/v1/config/test-embedding", tags=["配置"])
async def test_embedding_config(embedding_config: EmbeddingConfig):
    """
    测试Embedding配置是否可用

    Args:
        embedding_config: Embedding配置参数

    Returns:
        测试结果
    """
    try:
        from embedding_adapters import create_embedding_adapter

        logger.info("开始测试Embedding配置...")

        # 创建Embedding适配器
        embedding_adapter = create_embedding_adapter(
            interface_format=embedding_config.interface_format,
            api_key=embedding_config.api_key or "",
            base_url=embedding_config.base_url or "",
            model_name=embedding_config.model_name
        )

        # 发送测试请求
        test_text = "这是一个测试文本"
        embeddings = await asyncio.to_thread(embedding_adapter.embed_query, test_text)

        if embeddings and len(embeddings) > 0:
            logger.info(f"Embedding配置测试成功，向量维度: {len(embeddings)}")
            return {
                "success": True,
                "message": "Embedding配置测试成功",
                "dimension": len(embeddings)
            }
        else:
            return {
                "success": False,
                "message": "Embedding返回空向量"
            }

    except Exception as e:
        logger.error(f"Embedding配置测试失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }


@app.get("/api/v1/config/presets", tags=["配置"])
async def get_model_presets():
    """
    获取模型提供商预设配置

    返回所有支持的模型提供商的预设配置，包括：
    - OpenAI
    - OpenRouter
    - Azure OpenAI
    - Google Gemini
    - Anthropic Claude
    - DeepSeek
    - Moonshot (月之暗面)
    - 智谱AI (GLM)
    """
    return {
        "presets": MODEL_PROVIDER_PRESETS,
        "providers": list(MODEL_PROVIDER_PRESETS.keys())
    }


@app.post("/api/v1/knowledge/import", tags=["知识库"])
async def import_knowledge(
    filepath: str = Form(..., description="项目路径"),
    file: UploadFile = File(..., description="知识文件")
):
    """
    导入知识文件到向量库

    Args:
        filepath: 项目路径
        file: 上传的知识文件（支持txt、md等文本文件）

    Returns:
        导入结果
    """
    try:
        from novel_generator import import_knowledge_file
        import tempfile

        # 加载配置
        config = load_project_config(filepath)

        # 保存上传的文件到临时位置
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        logger.info(f"开始导入知识文件到项目: {filepath}")

        # 异步执行导入
        await asyncio.to_thread(
            import_knowledge_file,
            embedding_api_key=config["embedding"]["api_key"],
            embedding_url=config["embedding"]["base_url"],
            embedding_interface_format=config["embedding"]["interface_format"],
            embedding_model_name=config["embedding"]["model_name"],
            file_path=tmp_file_path,
            filepath=filepath
        )

        # 删除临时文件
        os.unlink(tmp_file_path)

        return {
            "success": True,
            "message": "知识文件导入成功"
        }

    except Exception as e:
        logger.error(f"导入知识文件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@app.post("/api/v1/knowledge/clear", tags=["知识库"])
async def clear_knowledge(filepath: str):
    """
    清空项目的向量库

    Args:
        filepath: 项目路径

    Returns:
        清空结果
    """
    try:
        from novel_generator import clear_vector_store

        project_dir = Path(filepath)
        if not project_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目目录不存在: {filepath}"
            )

        logger.info(f"清空项目向量库: {filepath}")

        # 异步执行清空操作
        success = await asyncio.to_thread(clear_vector_store, filepath)

        if success:
            return {
                "success": True,
                "message": "向量库已清空"
            }
        else:
            return {
                "success": False,
                "message": "向量库不存在或已清空"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空向量库失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/visualizations/generate", tags=["可视化"])
async def generate_visualizations(
    filepath: str,
    type: str = "all"  # all, timeline, relationship, heatmap
):
    """
    生成可视化图表

    Args:
        filepath: 项目路径
        type: 可视化类型（all/timeline/relationship/heatmap）

    Returns:
        生成的文件列表
    """
    try:
        from visualizations import generate_all_visualizations

        project_dir = Path(filepath)
        if not project_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目目录不存在: {filepath}"
            )

        logger.info(f"开始生成可视化图表: {type}")

        # 异步生成可视化
        results = await asyncio.to_thread(
            generate_all_visualizations,
            filepath=filepath
        )

        return {
            "success": True,
            "message": "可视化图表生成成功",
            "files": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成可视化失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成失败: {str(e)}"
        )


@app.get("/api/v1/visualizations/image", tags=["可视化"])
async def get_visualization_image(filepath: str, filename: str):
    """
    获取可视化图片

    Args:
        filepath: 项目路径
        filename: 图片文件名

    Returns:
        图片文件
    """
    try:
        from fastapi.responses import FileResponse

        project_dir = Path(filepath)
        vis_dir = project_dir / "visualizations"
        image_file = vis_dir / filename

        if not image_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"图片文件不存在: {filename}"
            )

        # 返回图片文件
        return FileResponse(
            path=str(image_file),
            media_type="image/png",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片失败: {e}", exc_info=True)
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
