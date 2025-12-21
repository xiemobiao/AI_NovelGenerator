# tests/test_logger_config.py
# -*- coding: utf-8 -*-
"""
日志系统测试
"""

import pytest
import logging
from pathlib import Path
from logger_config import NovelLogger, setup_logger, get_logger


class TestNovelLogger:
    """测试日志管理器"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        logger1 = NovelLogger()
        logger2 = NovelLogger()
        assert logger1 is logger2

    def test_setup_logger(self, temp_dir):
        """测试设置日志"""
        logger = setup_logger(
            name="TestLogger",
            log_dir=str(temp_dir),
            log_level=logging.DEBUG
        )

        assert logger is not None
        assert logger.name == "TestLogger"
        assert logger.level == logging.DEBUG

    def test_log_file_creation(self, temp_dir):
        """测试日志文件创建"""
        novel_logger = NovelLogger()
        logger = novel_logger.setup_logger(
            name="TestLogger2",
            log_dir=str(temp_dir)
        )

        logger.info("测试日志消息")

        # 检查日志文件是否创建
        log_files = list(Path(temp_dir).glob("novel_generator_*.log"))
        assert len(log_files) > 0

        # 检查日志内容
        log_content = log_files[0].read_text(encoding='utf-8')
        assert "测试日志消息" in log_content

    def test_get_logger(self):
        """测试获取日志器"""
        logger = get_logger()
        assert logger is not None

        logger_with_name = get_logger("SubModule")
        assert "SubModule" in logger_with_name.name
