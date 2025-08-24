# src/logger.py
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

# Import the new ColoredFormatter
from colorlog import ColoredFormatter
from src import config

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

FILE_BACKUP_COUNT: int = 10
FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB

class JsonFormatter(logging.Formatter):
    """Formats logs as JSON for file output."""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, DATETIME_FORMAT),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)

def get_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger
    
    log_file_path = _get_log_path(logger_name)
    _setup_logger(
        logger=logger,
        log_level=logging.DEBUG,
        log_file_path=log_file_path,
    )
    return logger

def _get_log_path(logger_name: str) -> Path:
    date = datetime.now(config.TIMEZONE).strftime(DATE_FORMAT)
    current_log_dir: Path = config.LOG_ROOT_DIR / date
    current_log_dir.mkdir(parents=True, exist_ok=True)
    return current_log_dir / f"{logger_name}.log"

def _setup_logger(
    logger: logging.Logger,
    log_level: int,
    log_file_path: Path,
):
    """Sets up the logger with a colored console handler and a JSON file handler."""
    logger.setLevel(log_level)

    # Console Handler with colors
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s] %(message)s",
        datefmt=DATETIME_FORMAT,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler with JSON
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=FILE_MAX_BYTES,
        backupCount=FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)