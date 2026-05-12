"""
日志配置模块
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(config: dict, logger_name: Optional[str] = None) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        config: 配置字典，包含 logging 部分
        logger_name: 日志器名称，默认为根日志器
    
    Returns:
        配置好的日志器
    """
    log_config = config.get("logging", {})
    
    # 日志级别
    level_str = log_config.get("level", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    
    # 日志文件
    log_file = log_config.get("file", "logs/automation.log")
    max_size = log_config.get("max_size_mb", 10) * 1024 * 1024  # 转换为字节
    backup_count = log_config.get("backup_count", 5)
    
    # 创建日志目录
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # 获取日志器
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"日志系统已初始化 (级别: {level_str}, 文件: {log_file})")
    
    return logger
