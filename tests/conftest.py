# tests/conftest.py
# -*- coding: utf-8 -*-
"""
Pytest配置和fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path


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
