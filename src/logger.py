# src/logger.py
import json
import logging
import logging.handlers  # 명시적 임포트 추가
from datetime import datetime
from pathlib import Path

from src import config


DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

FILE_BACKUP_COUNT: int = 10
FILE_MAX_BYTES: int = 10 * 1024 * 1024  # default: 10MB


class JsonFormatter(logging.Formatter):
    """JSON 형식으로 로그를 포맷팅하는 클래스"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, DATETIME_FORMAT),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        # extra 필드는 record의 __dict__에 동적으로 추가되므로,
        # 표준 속성이 아닌 키들을 식별하여 추가합니다.
        standard_keys = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())
        extra_data = {k: v for k, v in record.__dict__.items() if k not in standard_keys}
        if extra_data:
            log_data.update(extra_data)

        # exception 정보가 있다면 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def get_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)

    if logger.handlers:  # 핸들러가 이미 설정되었다면, 다시 설정하지 않음
        return logger

    log_file_path = _get_log_path(logger_name)
    _setup_logger(
        logger=logger,
        log_level=logging.DEBUG,
        log_file_path=log_file_path,
        log_file_max_bytes=FILE_MAX_BYTES,
        log_file_backup_count=FILE_BACKUP_COUNT,
    )
    return logger


def _get_log_path(logger_name: str) -> Path:
    """로그 파일의 전체 경로 반환"""
    # 날짜별로 로그가 모이도록
    date = datetime.now(config.TIMEZONE).strftime(DATE_FORMAT)
    current_log_dir: Path = config.LOG_ROOT_DIR / date
    current_log_dir.mkdir(parents=True, exist_ok=True)
    return current_log_dir / f"{logger_name}.log"


def _setup_logger(
    logger: logging.Logger,
    log_level: int,
    log_file_path: Path,
    log_file_max_bytes: int,
    log_file_backup_count: int,
):
    """logger 설정(콘솔 및 파일)"""
    logger.setLevel(log_level)

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s] %(message)s",
        datefmt=DATETIME_FORMAT,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 설정 (RotatingFileHandler 사용)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=log_file_max_bytes,
        backupCount=log_file_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
