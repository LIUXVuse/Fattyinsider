"""
日誌模組 - 提供應用程序日誌功能
"""
import logging
import sys
from typing import Dict, Any

from app.core.config import settings

# 日誌級別映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 獲取配置的日誌級別，默認為 INFO
log_level = LOG_LEVELS.get(settings.LOG_LEVEL.lower(), logging.INFO)

# 配置根日誌記錄器
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str) -> logging.Logger:
    """
    獲取指定名稱的日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        
    Returns:
        配置好的日誌記錄器實例
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger

# 創建應用程序日誌記錄器
app_logger = get_logger("fattyinsider") 