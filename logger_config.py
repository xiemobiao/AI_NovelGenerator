# logger_config.py
# -*- coding: utf-8 -*-
"""
日志配置模块
提供统一的日志配置和管理
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys


class NovelLogger:
    """小说生成器日志管理器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NovelLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.log_dir = None
            self.log_file = None
            self.logger = None
            self._initialized = True

    def setup_logger(
        self,
        name: str = "NovelGenerator",
        log_dir: Optional[str] = None,
        log_level: int = logging.INFO,
        console_output: bool = True,
        file_output: bool = True
    ) -> logging.Logger:
        """
        设置日志系统

        Args:
            name: 日志记录器名称
            log_dir: 日志文件目录
            log_level: 日志级别
            console_output: 是否输出到控制台
            file_output: 是否输出到文件

        Returns:
            配置好的logger对象
        """
        # 如果已经配置过，返回现有logger
        if self.logger is not None:
            return self.logger

        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # 清除已有的handlers
        self.logger.handlers.clear()

        # 定义日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 文件输出
        if file_output:
            if log_dir is None:
                log_dir = "./logs"

            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # 创建日志文件（按日期）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = self.log_dir / f"novel_generator_{timestamp}.log"

            file_handler = logging.FileHandler(
                self.log_file,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        return self.logger

    def get_logger(self) -> logging.Logger:
        """获取logger实例"""
        if self.logger is None:
            return self.setup_logger()
        return self.logger

    def set_level(self, level: int):
        """设置日志级别"""
        if self.logger:
            self.logger.setLevel(level)
            for handler in self.logger.handlers:
                handler.setLevel(level)

    def add_file_handler(self, filepath: str, level: int = logging.INFO):
        """添加额外的文件处理器"""
        if self.logger:
            handler = logging.FileHandler(filepath, encoding='utf-8')
            handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def get_latest_log_file(self) -> Optional[Path]:
        """获取最新的日志文件路径"""
        return self.log_file

    def cleanup_old_logs(self, keep_days: int = 7):
        """
        清理旧日志文件

        Args:
            keep_days: 保留最近几天的日志
        """
        if not self.log_dir or not self.log_dir.exists():
            return

        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=keep_days)

        for log_file in self.log_dir.glob("novel_generator_*.log"):
            try:
                # 从文件名提取日期
                file_date_str = log_file.stem.split('_')[2] + log_file.stem.split('_')[3]
                file_date = datetime.strptime(file_date_str, "%Y%m%d%H%M%S")

                if file_date < cutoff_date:
                    log_file.unlink()
                    if self.logger:
                        self.logger.info(f"删除旧日志文件: {log_file}")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"清理日志文件失败 {log_file}: {e}")


# 创建全局logger实例
_novel_logger = NovelLogger()


def setup_logger(
    name: str = "NovelGenerator",
    log_dir: Optional[str] = None,
    log_level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    便捷函数：设置日志系统

    Args:
        name: 日志记录器名称
        log_dir: 日志文件目录
        log_level: 日志级别
        console_output: 是否输出到控制台
        file_output: 是否输出到文件

    Returns:
        配置好的logger对象
    """
    return _novel_logger.setup_logger(
        name=name,
        log_dir=log_dir,
        log_level=log_level,
        console_output=console_output,
        file_output=file_output
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取logger实例

    Args:
        name: 可选的子模块名称

    Returns:
        logger对象
    """
    if name:
        return logging.getLogger(f"NovelGenerator.{name}")
    return _novel_logger.get_logger()


def set_log_level(level: int):
    """设置全局日志级别"""
    _novel_logger.set_level(level)


def cleanup_old_logs(keep_days: int = 7):
    """清理旧日志文件"""
    _novel_logger.cleanup_old_logs(keep_days)


if __name__ == "__main__":
    # 测试日志系统
    logger = setup_logger(log_level=logging.DEBUG)

    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")

    print(f"日志文件位置: {_novel_logger.get_latest_log_file()}")
