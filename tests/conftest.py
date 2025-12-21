# tests/conftest.py
# -*- coding: utf-8 -*-
"""
Pytest配置和fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from api_server import app
from models import User, Project, Chapter
from auth import hash_password

# 测试数据库URL（使用内存SQLite）
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# 创建测试引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 创建测试会话工厂
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def sample_novel_dir(temp_dir):
    """创建示例小说目录结构"""
    novel_dir = temp_dir / "test_novel"
    novel_dir.mkdir()

    # 创建示例文件
    (novel_dir / "Novel_architecture.txt").write_text(
        "这是小说架构内容\n核心种子：测试故事",
        encoding='utf-8'
    )

    (novel_dir / "Novel_directory.txt").write_text(
        "第1章：开始\n第2章：发展\n第3章：结束",
        encoding='utf-8'
    )

    # 创建几个章节
    for i in range(1, 4):
        chapter_file = novel_dir / f"chapter_{i}.txt"
        chapter_file.write_text(
            f"这是第{i}章的内容。\n" * 50,
            encoding='utf-8'
        )

    yield novel_dir


@pytest.fixture
def mock_llm_config():
    """模拟LLM配置"""
    return {
        "interface_format": "OpenAI",
        "api_key": "test-key",
        "base_url": "http://localhost:11434/v1",
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 4096,
        "timeout": 600
    }


@pytest.fixture
def mock_novel_config():
    """模拟小说配置"""
    return {
        "topic": "测试主题",
        "genre": "科幻",
        "num_chapters": 10,
        "word_number": 3000
    }


# ==================== 数据库Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """
    创建测试数据库会话
    每个测试函数使用独立的数据库会话
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # 清理所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    创建测试客户端
    覆盖get_db依赖，使用测试数据库
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session, test_user):
    """创建测试项目"""
    project = Project(
        name="测试小说",
        filepath="/test/novel",
        genre="奇幻",
        topic="魔法世界的冒险",
        num_chapters=10,
        user_id=test_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_chapter(db_session, test_project):
    """创建测试章节"""
    chapter = Chapter(
        chapter_number=1,
        title="第一章：开始",
        content="这是第一章的内容...",
        word_count=100,
        project_id=test_project.id
    )
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return chapter


@pytest.fixture
def auth_headers(client, test_user):
    """获取认证头"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user.username,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}
