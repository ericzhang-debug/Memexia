import logging
import sys
from pathlib import Path
from loguru import logger
from .config import Settings


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages and route them to Loguru.
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        # currentframe() may return None, so guard before accessing attributes
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def format_name(record):
    """自定义格式化函数，限制文件名长度为20个字符，显示最后20个字符"""
    name = record["name"]
    # 如果文件名长度超过20，只取最后20个字符
    if len(name) > 23:
        return "..." + name[-20:]
    return name


def setup_logging(settings: Settings):
    """
    Configure Loguru logger and intercept standard logging.
    """

    # Remove default loguru handler
    logger.remove()

    # Define log format - 使用自定义格式化函数
    file_log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <5}</level> | <cyan>{extra[short_name]:23}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    stdout_log_format = "<green>{time:MM-DD HH:mm:ss.SSS}</green> | <level>{level: <5}</level> | <cyan>{extra[short_name]:23}</cyan> - <level>{message}</level>"

    # Helper filter: inject short_name into record.extra and return True to keep the record
    def _inject_short_name(record) -> bool:
        extra = record.get("extra")
        if extra is None:
            record["extra"] = {}
        record["extra"]["short_name"] = format_name(record)
        return True

    # Add stdout handler
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=stdout_log_format,
        colorize=True,
        filter=_inject_short_name,
    )

    # Add file handler
    # Ensure logs directory exists
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)

    logger.add(
        log_path / "memexia_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # New file every day at midnight
        retention="30 days",  # Keep logs for 30 days
        level="DEBUG",  # Always log DEBUG to file
        format=file_log_format,
        encoding="utf-8",
        enqueue=True,  # Thread-safe
        filter=_inject_short_name,
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Hijack uvicorn and fastapi loggers
    # We need to make sure we don't duplicate logs if uvicorn is already configured
    # But since we force basicConfig with InterceptHandler, it should be fine.
    # Explicitly setting handlers for specific loggers ensures they use ours.
    for log_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "uvicorn.warning",
        "uvicorn.debug",
        "uvicorn.server",
        "fastapi",
    ]:
        logging_logger = logging.getLogger(log_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    return logger
