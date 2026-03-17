import logging
import os
from logging.handlers import TimedRotatingFileHandler


def get_logger(
    name: str,
    log_dir: str | None = None,
    level: int | None = None,
    when: str = "midnight",
    backup_count: int = 14,
) -> logging.Logger:
    """
    Create/retrieve a logger that writes to console + rotating file.

    - Rotates daily at midnight (default)
    - Keeps `backup_count` log files
    - Safe to call multiple times; handlers won't duplicate.
    """
    logger = logging.getLogger(name)
    if getattr(logger, "_configured_by_logging_utils", False):
        return logger

    effective_level = level or _parse_level(os.getenv("LOG_LEVEL", "INFO"))
    logger.setLevel(effective_level)
    logger.propagate = False

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    resolved_log_dir = log_dir or os.getenv("LOG_DIR") or os.path.join(base_dir, "logs")
    os.makedirs(resolved_log_dir, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_path = os.path.join(resolved_log_dir, f"{name}.log")
    file_handler = TimedRotatingFileHandler(
        file_path,
        when=when,
        backupCount=backup_count,
        encoding="utf-8",
        utc=True,
    )
    file_handler.setLevel(effective_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger._configured_by_logging_utils = True
    return logger


def _parse_level(level_str: str) -> int:
    s = (level_str or "").strip().upper()
    return {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }.get(s, logging.INFO)

